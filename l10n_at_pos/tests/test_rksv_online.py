import uuid
from datetime import datetime
from unittest import mock
import pytz
from odoo import fields
from odoo.tests.common import TransactionCase


class TestRKSVOnline(TransactionCase):
    ''' Test the enryption of RKSV '''

    def setUp(self):
        super().setUp()
        self.last_order = None

    def _to_utc(self, date):
        date_dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        date_dt = self.austrian_tz.localize(date_dt)
        return fields.Datetime.to_string(date_dt.astimezone(pytz.utc))

    def open_session(self, test_config):
        # get timezone
        self.austrian_tz = pytz.timezone("Europe/Berlin")

        # create product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'lst_price': 0.0,
        })

        # create journal for payment
        self.cash_journal = self.env['account.journal'].search([('type', '=', 'cash')], limit=1).copy()
        self.cash_payment_method = self.env['pos.payment.method'].create({
            'name': 'Cash Test',
            'journal_id': self.cash_journal.id,
        })

        # create config
        config_data = {
              'module_pos_restaurant': False,
              'payment_method_ids': [(6, 0, [self.cash_payment_method.id])],
        }
        config_data.update(test_config)
        self.config = self.env['pos.config'].create(config_data)
        self.config.action_asign_assign()

        # get tax
        self.tax_20 = self.env['account.tax'].search([('amount', '=', 20.0)], limit=1)
        self.tax_10 = self.env['account.tax'].search([('amount', '=', 10.0)], limit=1)

        # init session
        self.pos_session = self.env['pos.session'].create({'user_id': self.env.uid, 'config_id': self.config.id})
        self.pos_seq = 1

    def create_order(self, order_values):
        with mock.patch('requests.post') as post:
            response = mock.Mock()
            response.status_code = 200
            response.json.return_value = {
                'result': order_values['asign_dep']
            }
            post.return_value = response

            date_order = self._to_utc(order_values['date_order'])
            lines = []
            order_data = {
                'id': str(uuid.uuid4()),
                'data': {
                    'name': f'Order {self.pos_seq}',
                    'date_order': date_order,
                    'partner_id': None,
                    'fiscal_position_id': None,
                    'amount_return': 0.0,
                    'to_invoice': False,
                    'shipping_date': None,
                    'asign_state': 'u',
                    'asign_type': order_values['asign_type'],
                    'pos_session_id': self.pos_session.id,
                    'user_id': self.env.uid,
                    'amount_paid': order_values.get('amount_total', 0.0),
                    'amount_total': order_values.get('amount_total', 0.0),
                    'amount_tax': order_values.get('amount_tax', 0.0),
                    'sequence_number': self.pos_seq,
                    'statement_ids': [(0,0, {
                        'amount': order_values.get('amount_total', 0.0),
                        'uid': uuid.uuid4().hex,
                        'name': date_order,
                        'payment_method_id': self.cash_payment_method.id,
                        'payment_status': '',
                        'ticket': '',
                        'card_type': '',
                        'cardholder_name': '',
                        'transaction_id': '',
                    })],
                    'lines': lines
                }
            }

            for line in order_values.get('lines', []):
                line_amount = line.get('amount', 0.0)
                tax = line.get('tax', 0.0)
                tax_amount = round(line_amount * tax, 2)
                tax_ids = []
                if tax == 0.10:
                    tax_ids.append(self.tax_10.id)
                elif tax == 0.20:
                    tax_ids.append(self.tax_20.id)

                line_data = {
                    'id': str(uuid.uuid4()),
                    'name': line['name'],
                    'price_unit': line_amount,
                    'price_subtotal': line_amount - tax_amount,
                    'price_subtotal_incl': line_amount,
                    'discount': 0,
                    'product_id': self.product.id,
                    'full_product_name': line.get('name', 'Test'),
                    'qty': 1,
                    'tax_ids': [(6, 0, tax_ids)]
                }
                lines.append((0,0,line_data))

            res = self.env['pos.order'].create_from_ui([order_data])
            self.pos_seq += 1

            order = self.env['pos.order'].browse([r['id'] for r in res])

            # check the state
            self.assertEqual(len(order), 1, 'There should be one order created')
            self.assertEqual(order.asign_state, 's', 'The order should be signed')
            # check the turnover
            last_asign_counter = int(self.last_order.asign_counter) if self.last_order else 0
            self.assertEqual(order.asign_counter, str(last_asign_counter + int(order.amount_total*100)), 'Check the turnover')
            # check the QR code
            self.assertEqual(order.asign_qrcode, order_values['asign_qrcode'], 'The QR code should be correct')


            self.last_order = order
            return order

    def test_rksv_receipts_online(self):
        test_config = {
            'name': 'Test K08',
            'module_pos_restaurant': False,
            'asign_pid': 'K8',
            'asign_serial_hex': '584679a9',
            'asign_key': 'uOEQAfIsvFYzmMi3GFOFNgxRiodYksxg5o7Y+hGB9x4=',
            'asign_fid': 'ATU66181026',
            'asign_user': 'test',
            'asign_password': 'test',
            'asign_method': 'online'
        }

        test_data = [
            {
                "date_order": "2024-07-26 15:58:32",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF8xXzIwMjQtMDctMjZUMTU6NTg6MzJfMCwwMF8wLDAwXzAsMDBfMCwwMF8wLDAwX2xNdlZSciswcUx3PV81ODQ2NzlhOV9RcUJEZnN1Q0FoOD0.1j1i8_Vwr0Fyacw4KewCCnjfqSnP2MAFprNJl3zsHJgj-e8EKwR-N4GskQ6HqQiwZbhfSSgrcs70-LzwrKfDkw",
                "asign_qrcode": "_R1-AT1_K8_1_2024-07-26T15:58:32_0,00_0,00_0,00_0,00_0,00_lMvVRr+0qLw=_584679a9_QqBDfsuCAh8=_1j1i8/Vwr0Fyacw4KewCCnjfqSnP2MAFprNJl3zsHJgj+e8EKwR+N4GskQ6HqQiwZbhfSSgrcs70+LzwrKfDkw==",
                "asign_seq": 1,
                "asign_type": "s"
            },
            {
                "date_order": "2024-07-26 15:59:11",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF8yXzIwMjQtMDctMjZUMTU6NTk6MTFfMiw2MF8wLDAwXzAsMDBfMCwwMF8wLDAwX2RZeTJMdnFGTE4wPV81ODQ2NzlhOV9nRnVIYVdlS2lZaz0.k4wNp8l-e4WSn1pqvx4mcTFhegOwa7z31lB-44IpvI0dxGTMLaEx4mpeFJs_vwx2r-2_hN2BGK5Cye_AuvOTaw",
                "asign_qrcode": "_R1-AT1_K8_2_2024-07-26T15:59:11_2,60_0,00_0,00_0,00_0,00_dYy2LvqFLN0=_584679a9_gFuHaWeKiYk=_k4wNp8l+e4WSn1pqvx4mcTFhegOwa7z31lB+44IpvI0dxGTMLaEx4mpeFJs/vwx2r+2/hN2BGK5Cye/AuvOTaw==",
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
                "date_order": "2024-07-26 15:59:34",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF8zXzIwMjQtMDctMjZUMTU6NTk6MzRfMCwwMF8zLDAwXzAsMDBfMCwwMF8wLDAwXytCRzBGY1EzRGRrPV81ODQ2NzlhOV8wUG8yeFMvbUMwUT0.qIvLbjXUG8jNLR0ippDT8M0W729i5fZd3S5WvWSqVAmM-Ux5X5Cs4eMfNia9y2P8GimKKC8Gr5qnrWinT_jDfQ",
                "asign_qrcode": "_R1-AT1_K8_3_2024-07-26T15:59:34_0,00_3,00_0,00_0,00_0,00_+BG0FcQ3Ddk=_584679a9_0Po2xS/mC0Q=_qIvLbjXUG8jNLR0ippDT8M0W729i5fZd3S5WvWSqVAmM+Ux5X5Cs4eMfNia9y2P8GimKKC8Gr5qnrWinT/jDfQ==",
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
                "date_order": "2024-07-26 15:59:51",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF80XzIwMjQtMDctMjZUMTU6NTk6NTFfMCwwMF8tMywwMF8wLDAwXzAsMDBfMCwwMF9VMVJQCl81ODQ2NzlhOV83NXB3dHhNTU9UTT0.TRtn2n3VYqt8JB5Vuv0AnjBxfOcqx_mAxh9iyWEnZ68oFI4E7A2eTNzyD9GWbJLYF9e64YjWwzeO0biNPNHiXQ",
                "asign_qrcode": "_R1-AT1_K8_4_2024-07-26T15:59:51_0,00_-3,00_0,00_0,00_0,00_U1RP_584679a9_75pwtxMMOTM=_TRtn2n3VYqt8JB5Vuv0AnjBxfOcqx/mAxh9iyWEnZ68oFI4E7A2eTNzyD9GWbJLYF9e64YjWwzeO0biNPNHiXQ==",
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
                "date_order": "2024-07-26 16:00:10",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF81XzIwMjQtMDctMjZUMTY6MDA6MTBfMCwwMF8wLDAwXzAsMDBfMCwwMF8wLDAwX2Q1Tys4ZStnR1FFPV81ODQ2NzlhOV9Od0VzdU1ybFhRRT0.IAmeixQEguv16357U9S5csdtgqqsykIrXXDlBYhMF9hb8cebvgpQcBS9ImyrVwx4spNXHMTFLUXInWWy9YvsMA",
                "asign_qrcode": "_R1-AT1_K8_5_2024-07-26T16:00:10_0,00_0,00_0,00_0,00_0,00_d5O+8e+gGQE=_584679a9_NwEsuMrlXQE=_IAmeixQEguv16357U9S5csdtgqqsykIrXXDlBYhMF9hb8cebvgpQcBS9ImyrVwx4spNXHMTFLUXInWWy9YvsMA==",
                "asign_seq": 5,
                "asign_type": "0",
            },
            {
                "date_order": "2024-07-26 16:00:39",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF82XzIwMjQtMDctMjZUMTY6MDA6MzlfMiwyMF8wLDAwXzAsMDBfMCwwMF8wLDAwX1hGTjY1a1Z5SGFVPV81ODQ2NzlhOV9kenRoanhWQ3p3Yz0.zyFX1c-eTLhiYag_z41RyTVPglu_Y3ysSIzNdQ5MbiT8iVBLrjUcKFV9KPN5WfY42NncuHB0mQi_ekXuqWVgjw",
                "asign_qrcode": "_R1-AT1_K8_6_2024-07-26T16:00:39_2,20_0,00_0,00_0,00_0,00_XFN65kVyHaU=_584679a9_dzthjxVCzwc=_zyFX1c+eTLhiYag/z41RyTVPglu/Y3ysSIzNdQ5MbiT8iVBLrjUcKFV9KPN5WfY42NncuHB0mQi/ekXuqWVgjw==",
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
                "date_order": "2024-07-26 16:00:48",
                "asign_dep": "eyJhbGciOiJFUzI1NiJ9.X1IxLUFUMV9LOF83XzIwMjQtMDctMjZUMTY6MDA6NDhfMCwwMF8wLDAwXzAsMDBfLTQsODBfMCwwMF9JV0NkWFFTOHhOST1fNTg0Njc5YTlfWitnUW1hbFU1V2s9.8BgyKPR6MbQqHTScesGYCuX-2GYIIN0ZgYczTIH-Q1DW1HXjLVwRUKZ55spAs4BscrVwx_LGw6FqtaHAOfBQag",
                "asign_qrcode": "_R1-AT1_K8_7_2024-07-26T16:00:48_0,00_0,00_0,00_-4,80_0,00_IWCdXQS8xNI=_584679a9_Z+gQmalU5Wk=_8BgyKPR6MbQqHTScesGYCuX+2GYIIN0ZgYczTIH+Q1DW1HXjLVwRUKZ55spAs4BscrVwx/LGw6FqtaHAOfBQag==",
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


        # create session and orders
        self.open_session(test_config)
        for order in test_data:
            self.create_order(order)