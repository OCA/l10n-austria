# Copyright 2026 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import base64
from unittest import mock

import requests

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import TestAsignCommonMixin
from .test_cancel import TestAsignCancel


class TestAsignReceipt(TransactionCase, TestAsignCommonMixin):
    """The RKSV block on the server rendered receipt (Odoo 20)."""

    _sync_order = TestAsignCancel._sync_order
    _mock_sign = TestAsignCancel._mock_sign

    def setUp(self):
        super().setUp()
        self.open_session(
            {
                "name": "Receipt Test",
                "asign_enabled": True,
                "asign_pid": "K90",
                "asign_serial_hex": "abc123",
                "asign_key": base64.b64encode(b"0" * 32).decode(),
                "asign_cert": base64.b64encode(b"dummy").decode(),
                "asign_fid": "ATU12345675",
                "asign_user": "test",
                "asign_password": "test",
                "asign_method": "online",
            }
        )

    def test_signed_receipt(self):
        order = self._sync_order(1)
        self.assertEqual(order.asign_state, "s")
        self.assertTrue(order.asign_qrcode)

        data = order.order_receipt_generate_data()
        self.assertTrue(data["conditions"]["l10n_at_pos_rksv"])
        self.assertTrue(data["image"]["asign_qr_code"].startswith("data:image/png"))

        html = str(order.order_receipt_generate_html())
        self.assertIn("RKSV Daten", html)
        self.assertIn("K90", html)
        self.assertIn(order.asign_serial, html)
        self.assertIn(order.name, html)
        self.assertIn("STARTBELEG", html)
        self.assertIn(data["image"]["asign_qr_code"], html)
        self.assertNotIn("could not be signed", html)

    @mute_logger("odoo.addons.l10n_at_pos_rksv.models.pos_order")
    def test_unsigned_receipt(self):
        self._sync_order(1)
        fail = mock.patch(
            "requests.post", side_effect=requests.exceptions.ConnectionError()
        )
        order = self._sync_order(2, amount=5.0, sign_cm=fail)
        self.assertEqual(order.asign_state, "u")

        data = order.order_receipt_generate_data()
        self.assertNotIn("asign_qr_code", data["image"])

        html = str(order.order_receipt_generate_html())
        self.assertIn("could not be signed", html)
        self.assertNotIn("RKSV Daten", html)
