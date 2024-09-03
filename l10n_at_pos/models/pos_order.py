import logging
import hashlib
import struct
import base64
import pytz
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import requests
from odoo import _, fields, models, exceptions, api


_logger = logging.getLogger(__name__)


try:
    TIMEZONE_AT = pytz.timezone('Europe/Vienna')
except pytz.UnknownTimeZoneError:
    _logger.error('Timezone Europe/Vienna not found.')
    TIMEZONE_AT = None

def asign_b64urldecode_nopadding(v):
    missing_padding = len(v) % 4
    if missing_padding != 0:
        v += '=' * (4 - missing_padding)
    return base64.urlsafe_b64decode(v)

def asign_float(v):
    return f"{v:0.2f}".replace(".",",")

def asign_datetime(dt):
    utc_timestamp = pytz.utc.localize(dt, is_dst=False)  # UTC = no DST
    ldt = utc_timestamp.astimezone(TIMEZONE_AT) if TIMEZONE_AT else utc_timestamp
    return ldt.strftime("%Y-%m-%dT%H:%M:%S")

B64_STO = base64.b64encode(b'STO').decode()
B64_TRA = base64.b64encode(b'TRA').decode()

ASIGN_SUITE_ID = 'R1-AT1'
ASIGN_ENDPOINT = 'https://www.a-trust.at/asignrkonline/v2'
ASIGN_TIMEOUT = 30


class PosOrder(models.Model):
    _inherit = 'pos.order'

    asign_type = fields.Selection([('o', 'Order'),
                                   ('s', 'Start'),
                                   ('0', 'Null'),
                                   ('c', 'Cancel'),
                                   ('m', 'Mixed'),
                                   ('t', 'Training')], string="a.sign Type", index=True, readonly=True)

    asign_state = fields.Selection([('u', 'Unsigned'),
                                    ('s', 'Signed')],
                                    string='a.sign State',
                                    help=('The state of the RKSV signature. '
                                    'Unsigned means the signature is missing, signed means the signature is present. '
                                    'If not set, no signing is needed.'), index=True, readonly=True)

    asign_counter = fields.Char('a.sign Counter', help='The turnover counter of the RKSV signature.', readonly=True)
    asign_qrcode = fields.Char('a.sign QR-Code', help='The QR code of the RKSV signature.', index=True, readonly=True)
    asign_dep = fields.Text('a.sign DEP', help='The DEP of the RKSV signature export.', readonly=True)
    asign_serial = fields.Char('a.sign Serial', help='The serial number of the RKSV component.', readonly=True)
    asign_seq = fields.Integer('a.sign Sequence', help='The Sequence number of the RKSV signature export.', readonly=True, index=True)

    @api.model
    def _order_fields(self, ui_order):
        """ get fields from ui_order from pos """
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'asign_type': ui_order.get('asign_type'),
            'asign_state': ui_order.get('asign_state'),
            'asign_qrcode': ui_order.get('asign_qrcode'),
            'asign_serial': ui_order.get('asign_serial')
        })
        return res

    def _export_for_ui(self, order):
        """ ensure that order is exported with signature information """
        res = super(PosOrder, self)._export_for_ui(order)
        res.update({
            'asign_type': order.asign_type,
            'asign_state': order.asign_state,
            'asign_qrcode': order.asign_qrcode,
            'asign_serial': order.asign_serial,
            'asign_ref': order.name
        })
        return res

    def _compute_order_name(self):
        """ ensure that every signed order have a sequence number """
        if self.asign_state:
            return self.session_id.config_id.sequence_id._next()
        return super()._compute_order_name()

    def _compute_asign_seq(self):
        for order in self:
            seq_tokens = order.name.split('/')
            if len(seq_tokens) != 2:
                raise exceptions.ValidationError(_("Order name '%s' has invalid format (No Speration)", order.name))
            try:
                order.asign_seq = int(seq_tokens[1])
            except ValueError as e:
                raise exceptions.ValidationError(_("Order name '%s' has invalid format (No Number)", order.name)) from e

    def _asign_tax_amounts(self):
        """ Get the tax amounts for the RKSV signature with safe rounding """
        amount_total = self.currency_id.round(self.amount_total)
        res = {
            'normal': 0.0,
            'reduced1': 0.0,
            'reduced2': 0.0,
            'special': 0.0,
            'null': 0.0,
            'amount': amount_total,
            'turnover': int(amount_total*100)
        }

        # increment by type
        for line in self.lines:
            # per default normal tax is used
            asign_type = 'normal'
            # if no tax is set, use null
            if not line.tax_ids:
                asign_type = 'null'
            else:
                # check for special taxes
                tax_group = line.tax_ids.tax_group_id[:1]
                if tax_group.asign_type:
                    asign_type = tax_group.asign_type

            amount = self.currency_id.round(line.price_subtotal_incl)
            res[asign_type] += amount

        # never trust float
        # therfore let us check for rounding issues
        # and correct them
        correction_asign_type = None
        calc_amount_total = 0.0
        for amount_type in ('normal', 'reduced1', 'reduced2', 'special', 'null'):
            amount_type_total = res[amount_type]
            if amount_total:
                if not correction_asign_type:
                    correction_asign_type = amount_type
                calc_amount_total += amount_type_total
        # finaly make a safe round
        calc_amount_total = self.currency_id.round(calc_amount_total)
        # check if there is a difference.
        # If there is add it to the first best amount type
        diff = amount_total - calc_amount_total
        if diff and correction_asign_type:
            res[correction_asign_type] += diff
        # finally return the amounts
        return res

    def _asign_prepare_signature(self, last_order):
        """ prepare the signature data for the last signing step """

        config = self.session_id.config_id
        amounts = self._asign_tax_amounts()

        # calc the next turnover
        asign_counter = amounts['turnover']
        if last_order:
            asign_counter = asign_counter + int(last_order.asign_counter)

        # determine type and encode the turnover
        asign_type = 'o'
        if self.asign_type == 'c' or len(self.refunded_order_ids) != 0:
            asign_type = 'c'
            encoded_turnover = B64_STO
        elif self.asign_type == 't':
            asign_type = 't'
            encoded_turnover = B64_TRA
        else:
            # check 0 document
            if not amounts['amount']:
                asign_type = '0'
                # check if it is first
                if not last_order:
                    asign_type = 's'

            receipt_id = f'{config.asign_pid}{self.asign_seq}'
            turnover_ctr = hashlib.sha256(receipt_id.encode()).digest()[:16]
            turnover_bin = struct.pack(">qq", asign_counter, 0)
            cipher = Cipher(algorithms.AES(base64.b64decode(config.asign_key)), modes.CTR(turnover_ctr))
            encryptor = cipher.encryptor()
            encrypted_turnover = encryptor.update(turnover_bin) + encryptor.finalize()
            encoded_turnover = base64.b64encode(encrypted_turnover[:8]).decode()

        # build last hash for the chaining
        # if there is a last order use last signature, for the first order use the asign_pid
        last_hash = last_order.asign_dep if last_order else config.asign_pid
        last_hash = hashlib.sha256(last_hash.encode()).digest()[:8]
        last_hash = base64.b64encode(last_hash).decode()

        asign_data = [
            ASIGN_SUITE_ID,                     # 0
            config.asign_pid,                   # 1
            str(self.asign_seq),                # 2
            asign_datetime(self.date_order),    # 3
            asign_float(amounts['normal']),     # 4
            asign_float(amounts["reduced1"]),   # 5
            asign_float(amounts["reduced2"]),   # 6
            asign_float(amounts["null"]),       # 7
            asign_float(amounts["special"]),    # 8
            encoded_turnover,                   # 9
            config.asign_serial_hex,            # 10
            last_hash                           # 11
        ]
        asign_qrcode = f'_{"_".join(asign_data)}'
        return {
            'asign_serial': config.asign_serial_hex,
            'asign_counter': str(asign_counter),
            'asign_qrcode': asign_qrcode,
            'asign_type': asign_type
        }

    def _asign_create_signature(self, last_order):
        """ add the signature the the prepared data and return it """
        data = self._asign_prepare_signature(last_order)
        user, password = self.env['asign.cert']._get_login(data['asign_serial'])

        # build url
        url = f'{ASIGN_ENDPOINT}/{user}/Sign/JWS'
        payload = {
            'password': password,
            'jws_payload': data['asign_qrcode']
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        # post signation request
        resp = requests.post(url, json=payload, headers=headers, timeout=ASIGN_TIMEOUT)
        resp.raise_for_status()
        resp_data = resp.json()

        # check for error
        error = resp_data.get('error')
        if error:
            raise exceptions.ValidationError(_('Online RKSV signing error: %s', error))

        # check for result
        result = resp_data.get('result')
        if not result:
            raise exceptions.ValidationError(_('Online RKSV signing has no result'))

        # add signation
        signation = result.split(".")[-1]
        signation = asign_b64urldecode_nopadding(signation)
        signation = base64.b64encode(signation).decode()

        # finalize data
        data.update({
            'asign_state': 's',
            'asign_qrcode': f'{data["asign_qrcode"]}_{signation}',
            'asign_dep': result
        })
        return data

    def _asign_add_signature(self, limit=10):
        """ add a signature to the order """
        self.ensure_one()

        # assign sequence number
        self._compute_asign_seq()

        # get last signed sequence number
        cr = self.env.cr
        cr.execute('''SELECT asign_seq, o.id FROM pos_order o
                   INNER JOIN pos_session s ON s.id = o.session_id
                   WHERE s.config_id = %s
                     AND o.asign_state = 's'
                     AND o.asign_seq < %s
                   ORDER BY o.asign_seq DESC
                   LIMIT 1
                   ''', (self.session_id.config_id.id, self.asign_seq))

        rows = cr.fetchall()
        last_seq, last_order_id = rows[0] if rows else (0, None)
        last_order = self.browse(last_order_id) if last_order_id else self.browse()

        # check if the sequence number is valid
        if last_seq+1 == self.asign_seq or not last_order:
            orders = self
        else:
            # something is wrong try to search all not unsigned orders
            # and check if it is only an order mismatch
            unsigned_orders = self.search([('session_id.config_id', '=', self.session_id.config_id.id),('asign_seq', '>', last_seq),('asign_state','!=','s')], order='asign_seq ASC', limit=limit)
            if unsigned_orders[0].asign_seq == last_seq+1:
                orders = unsigned_orders
            else:
                # if there fits no order for the next sequence number, log an error
                # and cancel the signing
                _logger.error('**RKSV** Sequence number mismatch! Last signed order: %s, Current order: %s', last_order.name, self.name)
                return self.browse()

        # sign all unsigned orders, in the right order
        signed_orders = self.browse()
        for order in orders:
            # if the last order was signed, check if the current order is the next in sequence
            if signed_orders and order.asign_seq != last_order.asign_seq+1:
                _logger.error('**RKSV** Sequence number mismatch! Last signed order: %s, Current order: %s', last_order.name, order.name)
                return signed_orders

            try:
                signature = order._asign_create_signature(last_order)
                order.write(signature)
                order.flush_model()
                signed_orders += order
            except (exceptions.UserError, requests.exceptions.RequestException):
                # if there is an exception log it, but don't continue
                _logger.exception('**RKSV** Error during signing order %s', order.name)
                return signed_orders

            last_order = order

        return signed_orders

    def _process_saved_order(self, draft):
        res = super()._process_saved_order(draft)

        # if the order is paid, and not signed, we need to sign it
        if self.state == 'paid' and self.asign_state == 'u':
            self._asign_add_signature()

        return res

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_values = super(PosOrder, self).create_from_ui(orders, draft)
        if not draft:
            order_ids = [o['id'] for o in order_values]

            # query signature for all orders
            order_asign_values = self.env['pos.order'].search_read(domain=[('id', 'in', order_ids), ('asign_state', '=', 's')],
                            fields=['id',
                                    'asign_type',
                                    'asign_state',
                                    'asign_qrcode',
                                    'asign_serial',
                                    'name'], load=False)

            # build map
            if order_asign_values:
                order_asign_values = {o['id']: o for o in order_asign_values}

                # update order values with signature data
                for values in order_values:
                    asign_values = order_asign_values.get(values['id'], None)
                    if asign_values:
                        asign_ref = asign_values.pop('name')
                        asign_values['asign_ref'] = asign_ref
                        values.update(asign_values)

        return order_values