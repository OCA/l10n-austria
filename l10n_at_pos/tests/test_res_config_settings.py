import psycopg2
from odoo.tests.common import TransactionCase, Form


class TestRKSVConfig(TransactionCase):
    ''' Test configuration of RKSV settings '''

    def setUp(self):
        super().setUp()
        # create a certificate
        self.env['asign.cert'].create({
            'name': 'a',
            'cert_type': 'card'
        })

    def test_rksv_pid(self):
        ''' Test the prediction of next RKSV PID '''

        # for testing we need to reset the sequence
        self.env['pos.config'].search([]).write({
            'asign_enabled': False,
            'asign_pid': None
        })

        pos_config1 = self.env['pos.config'].create({'name': 'Test Config1', 'module_pos_restaurant': False, 'asign_serial_hex': 'a', 'asign_enabled': True})
        self.assertEqual(pos_config1.asign_method, 'online')
        self.assertEqual(pos_config1.asign_state, 'draft')
        self.assertEqual(pos_config1.asign_pid, 'K01')

        pos_config2 = pos_config1.copy()
        self.assertEqual(pos_config2.asign_method, 'online')
        self.assertEqual(pos_config2.asign_state, 'draft')
        self.assertEqual(pos_config2.asign_pid, 'K02')

        # flush before testing unique constraint
        self.env.flush_all()
        # test unique constraint
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            pos_config2.write({'asign_pid': 'K01'})
            self.env.flush_all()

    def test_rksv_setting_online(self):
        ''' Test the configuration of RKSV settings for online method '''
        pos_config1 = self.env['pos.config'].create({'name': 'Test Config1', 'module_pos_restaurant': False})

        # save form
        with Form(self.env['res.config.settings']) as form:
            form.pos_config_id = pos_config1
            form.asign_enabled = True
            form.asign_serial_hex = '0000000a'
            form.asign_pid = 'TESTK01'

        # save it again (to double check)
        with Form(self.env['res.config.settings']) as form:
            form.pos_config_id = pos_config1
            self.assertTrue(form.asign_enabled)
            self.assertEqual(form.asign_method, 'online')
            self.assertEqual(form.asign_state, 'draft')
            self.assertEqual(form.asign_serial_hex, 'a')
            self.assertTrue(form.asign_key, 'Check if key is generated')

        # check if sequence is updated
        self.assertEqual(pos_config1.sequence_id.name, pos_config1.asign_pid)
        self.assertEqual(pos_config1.sequence_id.prefix, f'{pos_config1.asign_pid}/')

        # check if CRC is updated
        self.assertTrue(pos_config1.asign_crc)

        # check if crc calculation is correct
        pos_config1.asign_key = 'l1wMFHeFBo4RpJClga03esiu5PJceAoNKwhUSNQJ+Mw='
        self.assertEqual(pos_config1.asign_crc, '25ZC')

        # check assign config
        pos_config1.action_asign_assign()
        self.assertEqual(pos_config1.asign_state, 'assigned')

        # reset config
        pos_config1.action_asign_reset()
        self.assertEqual(pos_config1.asign_state, 'draft')











