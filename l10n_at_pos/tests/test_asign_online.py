from odoo.tests.common import TransactionCase
from .common import TestAsignCommonMixin


class TestAsignOnline(TransactionCase, TestAsignCommonMixin):
    ''' Test the enryption of RKSV and online signing'''

    def test_asign_receipts_online(self):
        test_config = {
            'name': 'Test K10',
            'asign_pid': 'K10',
            'asign_serial_hex': '6fee0560',
            'asign_key': 'jC+8kFwYoKb8HCfx0bZSeEG0iu2RvKea03Qn9csb8/g=',
            'asign_fid': 'ATU56864003',
            'asign_user': 'test',
            'asign_password': 'test',
            'asign_method': 'online'
        }

        test_data = [
            {
                "date_order": "2024-08-06 15:28:52",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LMTBfMV8yMDI0LTA4LTA2VDE1OjI4OjUyXzAsMDBfMCwwMF8wLDAwXzAsMDBfMCwwMF9pdUY4c1NrOHpCaz1fNmZlZTA1NjBfMDF2d1QvOVg4Znc9.q7x9CtdGVHAETDidGCOov920vLOP4AaPk1I8UwZ0rFiZi0yIWkP1kripgeHiXRDtY3Ead8_A82bK3pT9v0PqKQ",
                "asign_qrcode": "_R1-AT1_K10_1_2024-08-06T15:28:52_0,00_0,00_0,00_0,00_0,00_iuF8sSk8zBk=_6fee0560_01vwT/9X8fw=_q7x9CtdGVHAETDidGCOov920vLOP4AaPk1I8UwZ0rFiZi0yIWkP1kripgeHiXRDtY3Ead8/A82bK3pT9v0PqKQ==",
                "asign_seq": 1,
                "asign_type": "s"
            },
            {
                "date_order": "2024-08-06 15:40:40",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LMTBfMl8yMDI0LTA4LTA2VDE1OjQwOjQwXzIsNjBfMCwwMF8wLDAwXzAsMDBfMCwwMF90Nlc5MlBLQnJxbz1fNmZlZTA1NjBfaXBHUlNCSXVHa0k9._xDyBxCf1J8s5maOjOi-rDHOBUiItEGiOKdMCDBUc4xzFIgPLsaYdBtJLi6jbQ8x3BdO7cXqNpoacQnQmca4aw",
                "asign_qrcode": "_R1-AT1_K10_2_2024-08-06T15:40:40_2,60_0,00_0,00_0,00_0,00_t6W92PKBrqo=_6fee0560_ipGRSBIuGkI=_/xDyBxCf1J8s5maOjOi+rDHOBUiItEGiOKdMCDBUc4xzFIgPLsaYdBtJLi6jbQ8x3BdO7cXqNpoacQnQmca4aw==",
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
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LMTBfM18yMDI0LTA4LTA2VDE1OjQzOjQ0XzAsMDBfMywwMF8wLDAwXzAsMDBfMCwwMF92bk5Idkt4TDBHYz1fNmZlZTA1NjBfS1FaUldzV1htSGM9.5uqqZN782Tr7-zI7-5U1OCN2AGe_mcn5Lr-QoGhsf9K_L2NyM6FajFxbe7BAlv3gvv_eU9zuArlJ68P-YJdtBQ",
                "asign_qrcode": "_R1-AT1_K10_3_2024-08-06T15:43:44_0,00_3,00_0,00_0,00_0,00_vnNHvKxL0Gc=_6fee0560_KQZRWsWXmHc=_5uqqZN782Tr7+zI7+5U1OCN2AGe/mcn5Lr+QoGhsf9K/L2NyM6FajFxbe7BAlv3gvv/eU9zuArlJ68P+YJdtBQ==",
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
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LMTBfNF8yMDI0LTA4LTA2VDE1OjQ2OjA3XzAsMDBfLTMsMDBfMCwwMF8wLDAwXzAsMDBfVTFSUApfNmZlZTA1NjBfNVo4SEgrNkJmeVU9.Fyy05ImnMlKSglOMeLwliI-UlY-87BvTtCJ8L3IlNGsOBWezfvNiPB1FepKZHN4ALy3aKi1usVu3aIkCS0hsnA",
                "asign_qrcode": "_R1-AT1_K10_4_2024-08-06T15:46:07_0,00_-3,00_0,00_0,00_0,00_U1RP_6fee0560_5Z8HH+6BfyU=_Fyy05ImnMlKSglOMeLwliI+UlY+87BvTtCJ8L3IlNGsOBWezfvNiPB1FepKZHN4ALy3aKi1usVu3aIkCS0hsnA==",
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
            # {
            #     "date_order": "2024-07-26 16:00:10",
            #     "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF81XzIwMjQtMDctMjZUMTY6MDA6MTBfMCwwMF8wLDAwXzAsMDBfMCwwMF8wLDAwX2Q1Tys4ZStnR1FFPV81ODQ2NzlhOV9Od0VzdU1ybFhRRT0.IAmeixQEguv16357U9S5csdtgqqsykIrXXDlBYhMF9hb8cebvgpQcBS9ImyrVwx4spNXHMTFLUXInWWy9YvsMA",
            #     "asign_qrcode": "_R1-AT1_K8_5_2024-07-26T16:00:10_0,00_0,00_0,00_0,00_0,00_d5O+8e+gGQE=_584679a9_NwEsuMrlXQE=_IAmeixQEguv16357U9S5csdtgqqsykIrXXDlBYhMF9hb8cebvgpQcBS9ImyrVwx4spNXHMTFLUXInWWy9YvsMA==",
            #     "asign_seq": 5,
            #     "asign_type": "0",
            # },
            # {
            #     "date_order": "2024-07-26 16:00:39",
            #     "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF82XzIwMjQtMDctMjZUMTY6MDA6MzlfMiwyMF8wLDAwXzAsMDBfMCwwMF8wLDAwX1hGTjY1a1Z5SGFVPV81ODQ2NzlhOV9kenRoanhWQ3p3Yz0.zyFX1c-eTLhiYag_z41RyTVPglu_Y3ysSIzNdQ5MbiT8iVBLrjUcKFV9KPN5WfY42NncuHB0mQi_ekXuqWVgjw",
            #     "asign_qrcode": "_R1-AT1_K8_6_2024-07-26T16:00:39_2,20_0,00_0,00_0,00_0,00_XFN65kVyHaU=_584679a9_dzthjxVCzwc=_zyFX1c+eTLhiYag/z41RyTVPglu/Y3ysSIzNdQ5MbiT8iVBLrjUcKFV9KPN5WfY42NncuHB0mQi/ekXuqWVgjw==",
            #     "asign_seq": 6,
            #     "asign_type": "o",
            #     "amount_total": 2.20,
            #     "amount_tax": 0.37,
            #     "lines": [
            #         {
            #             "name": "Birnensaft",
            #             "tax": 0.20,
            #             "amount": 2.60,
            #         },
            #         {
            #             "name": "Minus Pfand",
            #             "tax": 0.20,
            #             "amount": -0.40
            #         }
            #     ]
            # },
            # {
            #     "date_order": "2024-07-26 16:00:48",
            #     "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF83XzIwMjQtMDctMjZUMTY6MDA6NDhfMCwwMF8wLDAwXzAsMDBfLTQsODBfMCwwMF9JV0NkWFFTOHhOST1fNTg0Njc5YTlfWitnUW1hbFU1V2s9.8BgyKPR6MbQqHTScesGYCuX-2GYIIN0ZgYczTIH-Q1DW1HXjLVwRUKZ55spAs4BscrVwx_LGw6FqtaHAOfBQag",
            #     "asign_qrcode": "_R1-AT1_K8_7_2024-07-26T16:00:48_0,00_0,00_0,00_-4,80_0,00_IWCdXQS8xNI=_584679a9_Z+gQmalU5Wk=_8BgyKPR6MbQqHTScesGYCuX+2GYIIN0ZgYczTIH+Q1DW1HXjLVwRUKZ55spAs4BscrVwx/LGw6FqtaHAOfBQag==",
            #     "asign_seq": 7,
            #     "asign_type": "o",
            #     "amount_total": -4.80,
            #     "lines": [
            #         {
            #             "name": "Auszahlung",
            #             "amount": -4.80
            #         }
            #     ]
            # }
        ]


        # create session and orders
        self.open_session(test_config)
        for order in test_data:
            self.create_order(order)