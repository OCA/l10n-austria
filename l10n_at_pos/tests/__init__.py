from odoo import tools

from . import test_res_config_settings
from . import test_asign_online

if tools.config.get('test_asign'):
    from . import test_int_asign_online
