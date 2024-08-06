import shutil
from odoo.tools import config
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.oerp_util.tests.common import TestMixin
from .common import TestAsignCommonMixin
from .regcheck.regcheck import RegChecker


@tagged('integration', '-standard')
class TestIntAsignOnline(TransactionCase, TestAsignCommonMixin, TestMixin):
    ''' Test the enryption of RKSV '''

    def test_asign_int_receipts_online(self):
        test_config = {
            'name': 'Test',
            'asign_pid': config['test_asign_pid'],
            'asign_serial_hex': config['test_asign_serial_hex'],
            'asign_key': config['test_asign_key'],
            'asign_cert': config['test_asign_cert'],
            'asign_fid': config['test_asign_fid'],
            'asign_user': config['test_asign_user'],
            'asign_password': config['test_asign_password'],
            'asign_method': 'online'
        }

        test_data = [
            {
                "date_order": "2024-08-06 15:28:52",
                "asign_seq": 1,
                "asign_type": "s"
            },
            {
                "date_order": "2024-08-06 15:40:40",
                "asign_seq": 2,
                "asign_type": "o",
                "amount_total": 2.60,
                "amount_tax": 0.43,
                "lines": [
                    {
                        "name": "Apfelsaft",
                        "tax": 0.20,
                        "amount": 2.60,
                    }
                ]
            },
            {
                "date_order": "2024-08-06 15:43:44",
                "asign_seq": 3,
                "asign_type": "o",
                "amount_total": 3.0,
                "amount_tax": 0.27,
                "lines": [
                    {
                        "name": "Leberaustrich",
                        "tax": 0.10,
                        "amount": 3.0,
                    }
                ]
            },
            {
                "date_order": "2024-08-06 15:46:07",
                "asign_seq": 4,
                "asign_type": "c",
                "amount_total": -3.0,
                "amount_tax": -0.27,
                "lines": [
                    {
                        "name": "Leberaustrich",
                        "tax": 0.10,
                        "amount": -3.0,
                    }
                ]
            },
            {
                "date_order": "2024-08-06 16:00:10",
                "asign_seq": 5,
                "asign_type": "0",
            },
            {
                "date_order": "2024-08-06 16:15:39",
                "asign_seq": 6,
                "asign_type": "o",
                "amount_total": 2.20,
                "amount_tax": 0.37,
                "lines": [
                    {
                        "name": "Birnensaft",
                        "tax": 0.20,
                        "amount": 2.60,
                    },
                    {
                        "name": "Minus Pfand",
                        "tax": 0.20,
                        "amount": -0.40
                    }
                ]
            },
            {
                "date_order": "2024-08-06 17:00:48",
                "asign_seq": 7,
                "asign_type": "o",
                "amount_total": -4.80,
                "lines": [
                    {
                        "name": "Auszahlung",
                        "amount": -4.80
                    }
                ]
            }
        ]

        # open session
        self.open_session(test_config)

        # create order
        for order in test_data:
            self._create_order(order)

        # remove directory
        regcheck_dir = self.getDownloadPath('asign_test')
        shutil.rmtree(regcheck_dir, ignore_errors=True)

        # save dep
        dep_export = self.pos_config._asign_dep_export()
        self.saveTestData('asign_test/dep.json', dep_export)

        # create regcheck
        regcheck = RegChecker(regcheck_dir, crypto_config={
            "base64AESKey" : self.pos_config.asign_key,
            "certificateOrPublicKeyMap" : {
                self.pos_config.asign_serial_hex : {
                    "id" : self.pos_config.asign_serial_hex,
                    "signatureDeviceType" : "CERTIFICATE",
                    "signatureCertificateOrPublicKey" : self.pos_config.asign_cert.decode()
                }
            }
        })

        self.assertTrue(regcheck.check(), 'Check if DEP is valid')
