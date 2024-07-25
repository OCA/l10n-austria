# update tax groups

def post_init_hook(env):
    TaxGroup = env['account.tax.group']

    # set asign_type for 0% tax group to null
    TaxGroup.search([('name', '=', '0%'), ('country_id.code', '=', 'AT')]).write({
        'asign_type': 'null'
    })

    # set asign_type for 10% tax group to reduced1
    TaxGroup.search([('name', '=', '10%'), ('country_id.code', '=', 'AT')]).write({
        'asign_type': 'reduced1'
    })

      # set asign_type for 13% tax group to reduced2
    TaxGroup.search([('name', '=', '13%'), ('country_id.code', '=', 'AT')]).write({
        'asign_type': 'reduced2'
    })

    # set asign_type for special taxes 19% and 12%
    TaxGroup.search([('name', 'in', ('19%', '12%')), ('country_id.code', '=', 'AT')]).write({
        'asign_type': 'special'
    })