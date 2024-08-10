import uuid
from datetime import datetime
from unittest import mock
import pytz
from odoo import fields


class TestAsignCommonMixin():
    ''' Common class for tests related to the a.sign integration '''

    def _to_utc(self, date):
        date_dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        date_dt = self.austrian_tz.localize(date_dt)
        return fields.Datetime.to_string(date_dt.astimezone(pytz.utc))

    def open_session(self, test_config):
        # get timezone
        self.last_order = None
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

        # get/create certificate
        asign_cert = test_config.pop('asign_cert', None)
        asign_user = test_config.pop('asign_user', None)
        asign_password = test_config.pop('asign_password', None)
        if asign_cert:
            AsignCert = self.env['asign.cert']
            self.asign_cert = AsignCert.search([('serial_hex', '=', test_config['asign_serial_hex'])], limit=1)
            if not self.asign_cert:
                self.asign_cert = self.env['asign.cert'].create({
                    'name': test_config['asign_serial_hex'],
                    'cert': asign_cert,
                    'user': asign_user,
                    'password': asign_password
                })

        # create config
        config_data = {
              'module_pos_restaurant': False,
              'payment_method_ids': [(6, 0, [self.cash_payment_method.id])],
        }
        config_data.update(test_config)
        self.pos_config = self.env['pos.config'].create(config_data)
        self.pos_config.action_asign_assign()

        # get tax
        self.tax_20 = self.env['account.tax'].search([('amount', '=', 20.0)], limit=1)
        self.tax_10 = self.env['account.tax'].search([('amount', '=', 10.0)], limit=1)

        # init session
        self.pos_session = self.env['pos.session'].create({'user_id': self.env.uid, 'config_id': self.pos_config.id})
        self.pos_seq = 1

    def _create_order(self, order_values):
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
        # check if serial is set
        self.assertEqual(order.asign_serial, self.asign_cert.serial_hex, 'The serial should be set')
        # check the turnover
        last_asign_counter = int(self.last_order.asign_counter) if self.last_order else 0
        self.assertEqual(order.asign_counter, str(last_asign_counter + int(order.amount_total*100)), 'Check the turnover')

        self.last_order = order
        return order

    def create_order(self, order_values):
        with mock.patch('requests.post') as post:
            response = mock.Mock()
            response.status_code = 200
            response.json.return_value = {
                'result': order_values['asign_dep']
            }
            post.return_value = response
            order = self._create_order(order_values)
            self.assertEqual(order.asign_qrcode, order_values['asign_qrcode'], 'The QR code should be correct')