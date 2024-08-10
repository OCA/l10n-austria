from odoo import tools

from . import test_res_config_settings

if tools.config.get('test_asign'):
    from . import test_asign_online
