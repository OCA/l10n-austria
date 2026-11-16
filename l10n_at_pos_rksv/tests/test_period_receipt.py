# Copyright 2026 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import base64
from datetime import datetime
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from .common import TestAsignCommonMixin

# Fake JWS result; only the base64url signature part is decoded by
# _asign_create_signature.
JWS_FAKE = "eyJhbGciOiJFUzI1NiJ9.cGF5bG9hZA.c2lnbmF0dXJl"


class TestAsignPeriodReceipt(TransactionCase, TestAsignCommonMixin):
    """Month/year receipts, their crons and the DEP export button."""

    def setUp(self):
        super().setUp()
        self.create_config(
            {
                "name": "Period Test",
                "asign_enabled": True,
                "asign_pid": "K91",
                "asign_serial_hex": "abc123",
                "asign_key": base64.b64encode(b"0" * 32).decode(),
                "asign_cert": base64.b64encode(b"dummy").decode(),
                "asign_fid": "ATU12345675",
                "asign_user": "test",
                "asign_password": "test",
                "asign_method": "online",
            }
        )
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"result": JWS_FAKE}
        patcher = mock.patch("requests.post", return_value=response)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _receipts(self, asign_type):
        return self.env["pos.order"].search(
            [("config_id", "=", self.pos_config.id), ("asign_type", "=", asign_type)]
        )

    def test_create_month_receipt(self):
        # Case 1: start receipt, then month receipt (signed, seq 1 -> 2)
        start = self.pos_config._asign_create_zero_receipt()
        month = self.pos_config._asign_create_zero_receipt("month")
        self.assertEqual(start.asign_type, "s")
        self.assertEqual(month.asign_type, "month")
        self.assertEqual(month.asign_state, "s")
        self.assertEqual(month.asign_seq, start.asign_seq + 1)
        # Case 2: invalid receipt type raises
        with self.assertRaises(UserError):
            self.pos_config._asign_create_zero_receipt("bogus")

    def test_cron_month_receipt_idempotent(self):
        # Case 1: no start receipt yet -> cron creates nothing
        self.pos_config._cron_asign_month_receipt()
        self.assertFalse(self._receipts("month"))
        # Case 2: with start receipt, two runs -> one month receipt
        self.pos_config._asign_create_zero_receipt()
        self.pos_config._cron_asign_month_receipt()
        self.pos_config._cron_asign_month_receipt()
        self.assertEqual(len(self._receipts("month")), 1)

    def test_check_receipt(self):
        # Case 1: signed fake receipt has a consistent signature
        start = self.pos_config._asign_create_zero_receipt()
        self.assertTrue(self.pos_config._asign_check_receipt(start))
        # Case 2: broken JWS fails and is posted on the receipt
        start.asign_dep = "broken"
        self.assertFalse(self.pos_config._asign_check_receipt(start))
        self.assertIn("check failed", start.message_ids[0].body)

    def test_action_asign_dep_export(self):
        action = self.pos_config.action_asign_dep_export()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("download=true", action["url"])

    def test_period_start_vienna(self):
        # Case 1: 30 Nov 23:30 UTC is already 1 Dec in Vienna (UTC+1)
        now_utc = datetime(2026, 11, 30, 23, 30)
        month = self.env["pos.config"]._asign_period_start("month", now_utc)
        year = self.env["pos.config"]._asign_period_start("year", now_utc)
        self.assertEqual(month, datetime(2026, 11, 30, 23, 0))  # 1 Dec 00:00 CET
        self.assertEqual(year, datetime(2025, 12, 31, 23, 0))  # 1 Jan 00:00 CET

    def test_check_called_for_start_and_year_only(self):
        config = self.pos_config
        with mock.patch.object(
            type(config), "_asign_check_receipt", autospec=True
        ) as check:
            config._asign_create_zero_receipt()  # start
            config._asign_create_zero_receipt("month")
            self.assertEqual(check.call_count, 1)
            config._asign_create_zero_receipt("year")
            self.assertEqual(check.call_count, 2)
