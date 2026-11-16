# Copyright 2026 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import base64
from datetime import datetime
from unittest import mock

from odoo import fields
from odoo.tests.common import TransactionCase

from .common import TestAsignCommonMixin

# Fake JWS result; only the base64url signature part is decoded by
# _asign_create_signature.
JWS_FAKE = "eyJhbGciOiJFUzI1NiJ9.cGF5bG9hZA.c2lnbmF0dXJl"

# Naive UTC "now" values; Vienna is UTC+1 in winter.
NOV_15 = datetime(2026, 11, 15, 12, 0)
NOV_30_UTC_EARLY = datetime(2026, 11, 30, 22, 30)  # 23:30 Vienna, still November
NOV_30_UTC_LATE = datetime(2026, 11, 30, 23, 30)  # 00:30 Vienna on 1 Dec
DEC_1 = datetime(2026, 12, 1, 6, 0)
JAN_1 = datetime(2027, 1, 1, 6, 0)


class TestAsignPeriodReceipt(TransactionCase, TestAsignCommonMixin):
    """Month receipts, their cron and the DEP export button."""

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

    def _at(self, when):
        """Run code with ``fields.Datetime.now()`` fixed to ``when`` (naive UTC)."""
        return mock.patch.object(fields.Datetime, "now", return_value=when)

    def test_cron_month_receipt_month_end(self):
        # Scene: start receipt on 15 Nov 2026; month ends at 1 Dec 00:00 Vienna.
        with self._at(NOV_15):
            # Case 1: no start receipt yet -> cron creates nothing
            self.pos_config._cron_asign_month_receipt()
            self.assertFalse(self._receipts("month"))
            self.pos_config._asign_create_zero_receipt()
            # Case 2: still in the start month -> no month has ended
            self.pos_config._cron_asign_month_receipt()
            self.assertFalse(self._receipts("month"))
        with self._at(DEC_1):
            # Case 3: on the 1st, receipt for ended November, second run none
            self.pos_config._cron_asign_month_receipt()
            self.pos_config._cron_asign_month_receipt()
            self.assertEqual(len(self._receipts("month")), 1)

    def test_cron_month_receipt_vienna_boundary(self):
        with self._at(NOV_15):
            self.pos_config._asign_create_zero_receipt()
        # Case 1: 30 Nov 22:30 UTC is 23:30 in Vienna, month not over -> none
        with self._at(NOV_30_UTC_EARLY):
            self.pos_config._cron_asign_month_receipt()
        self.assertFalse(self._receipts("month"))
        # Case 2: 30 Nov 23:30 UTC is already 1 Dec in Vienna -> created
        with self._at(NOV_30_UTC_LATE):
            self.pos_config._cron_asign_month_receipt()
        self.assertEqual(len(self._receipts("month")), 1)

    def test_month_start_dst(self):
        # Case 1: 26 Oct (CET) -> 1 Oct 00:00 is still CEST = 30 Sep 22:00 UTC
        start = self.pos_config._asign_month_start(datetime(2026, 10, 26, 10, 0))
        self.assertEqual(start, datetime(2026, 9, 30, 22, 0))

    def test_check_receipt(self):
        # Case 1: signed fake receipt has a consistent signature
        start = self.pos_config._asign_create_zero_receipt()
        self.assertTrue(self.pos_config._asign_check_receipt(start))
        # Case 2: broken JWS fails and is posted on the receipt
        start.asign_dep = "broken"
        self.assertFalse(self.pos_config._asign_check_receipt(start))
        self.assertIn("check failed", start.message_ids[0].body)

    def test_check_called_for_start_and_december_month_receipt(self):
        config = self.pos_config
        with mock.patch.object(
            type(config), "_asign_check_receipt", autospec=True
        ) as check:
            with self._at(NOV_15):
                config._asign_create_zero_receipt()  # start
            self.assertEqual(check.call_count, 1)
            # Case 1: month receipt of November (created in December): no check
            with self._at(DEC_1):
                config._asign_create_zero_receipt("month")
            self.assertEqual(check.call_count, 1)
            # Case 2: month receipt of December (created in January): checked
            with self._at(JAN_1):
                config._asign_create_zero_receipt("month")
            self.assertEqual(check.call_count, 2)
