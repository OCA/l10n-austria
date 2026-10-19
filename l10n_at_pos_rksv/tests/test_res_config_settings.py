# Copyright 2024 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import psycopg2

from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestRksvConfig(TransactionCase):
    """Test configuration of RKSV settings."""

    def setUp(self):
        super().setUp()
        self.env["asign.cert"].create({"name": "a", "cert_type": "card"})

    @mute_logger("odoo.sql_db")
    def test_rksv_pid(self):
        """Next RKSV POS-ID is predicted correctly and unique per company."""
        self.env["pos.config"].search([]).write(
            {"asign_enabled": False, "asign_pid": None}
        )

        pos_config1 = self.env["pos.config"].create(
            {
                "name": "Test Config1",
                "module_pos_restaurant": False,
                "asign_serial_hex": "a",
                "asign_enabled": True,
                "asign_fid": "AT1234567890",
            }
        )

        self.assertEqual(pos_config1.asign_method, "online")
        self.assertEqual(pos_config1.asign_state, "draft")
        self.assertEqual(pos_config1.asign_pid, "K01")

        pos_config2 = pos_config1.copy()
        self.assertEqual(pos_config2.asign_method, "online")
        self.assertEqual(pos_config2.asign_state, "draft")
        self.assertEqual(pos_config2.asign_pid, "K02")

        self.env.flush_all()

        with self.assertRaises(psycopg2.errors.UniqueViolation):
            pos_config2.write({"asign_pid": "K01"})
            self.env.flush_all()

    def test_rksv_copy_signs_under_its_own_pos_id(self):
        """A copied POS gets its own order sequence, stamped when assigned.

        The sequences themselves are never copied - the core hands every new
        POS fresh ones - but their prefix carries the fiscal POS id, and that
        was only written by the settings wizard. A POS created by copying
        therefore used to sign receipts without any POS id.
        """
        self.env["pos.config"].search([]).write(
            {"asign_enabled": False, "asign_pid": None}
        )

        source = self.env["pos.config"].create(
            {
                "name": "Test Config1",
                "module_pos_restaurant": False,
                "asign_serial_hex": "a",
                "asign_enabled": True,
                "asign_fid": "AT1234567890",
            }
        )
        source.action_asign_assign()
        self.assertEqual(source.order_seq_id.prefix, "K01/")

        copied = source.copy()
        self.assertEqual(copied.asign_pid, "K02")
        self.assertEqual(copied.asign_state, "draft")
        self.assertFalse(
            copied.asign_seq_id, "receipt sequence comes with the assignment"
        )
        self.assertNotEqual(copied.order_seq_id, source.order_seq_id)

        copied.action_asign_assign()
        self.assertEqual(copied.order_seq_id.name, "K02")
        self.assertEqual(copied.order_seq_id.prefix, "K02/")
        self.assertEqual(copied.order_seq_id.implementation, "no_gap")
        self.assertFalse(copied.order_seq_id.suffix)
        self.assertTrue(copied.asign_seq_id)
        self.assertNotEqual(copied.asign_seq_id, source.asign_seq_id)
        self.assertEqual(source.order_seq_id.prefix, "K01/", "source stays untouched")

    def test_rksv_setting_online(self):
        """Settings wizard exposes RKSV fields and updates the POS config."""
        pos_config1 = self.env["pos.config"].create(
            {"name": "Test Config1", "module_pos_restaurant": False}
        )

        with Form(self.env["res.config.settings"]) as form:
            form.pos_config_id = pos_config1
            form.asign_enabled = True
            form.asign_serial_hex = "0000000a"
            form.asign_pid = "TESTK01"
            form.asign_fid = "AT1234567890"

        with Form(self.env["res.config.settings"]) as form:
            form.pos_config_id = pos_config1
            self.assertTrue(form.asign_enabled)
            self.assertEqual(form.asign_method, "online")
            self.assertEqual(form.asign_state, "draft")
            self.assertEqual(form.asign_serial_hex, "a")
            self.assertTrue(form.asign_key, "Encryption key must be generated")

        self.assertEqual(pos_config1.order_seq_id.name, pos_config1.asign_pid)
        self.assertEqual(pos_config1.order_seq_id.prefix, f"{pos_config1.asign_pid}/")

        self.assertTrue(pos_config1.asign_crc)

        pos_config1.asign_key = "l1wMFHeFBo4RpJClga03esiu5PJceAoNKwhUSNQJ+Mw="
        self.assertEqual(pos_config1.asign_crc, "25ZC")

        pos_config1.action_asign_assign()
        self.assertEqual(pos_config1.asign_state, "assigned")

        pos_config1.action_asign_reset()
        self.assertEqual(pos_config1.asign_state, "draft")
