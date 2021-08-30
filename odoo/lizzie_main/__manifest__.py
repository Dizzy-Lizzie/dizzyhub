{
    'name': 'Lizzie Main',
    'version': '0.1',
    'summary': 'Top level controlling modlue for Lizzie Odoo Instance',
    'sequence': 10,
    'description': """
Configures Odoo core and other modules for site specific functions of the 
Dizzie lizze site.
Used to bootstrap new environments and update existing ones.

Order of depends is Odoo core modules, then 3rd party, lastly internally
developed modules.
    """,
    'category': 'Tools',
    'website': 'https://github.com/etherealite',
    'depends': [
        'contacts',
        'sale_management',
        'sale_product_matrix',
        'stock',
        'website_sale',
        'disable_odoo_online',
        'product_code_unique',
        # 'product_variant_default_code',
        'remove_odoo_enterprise',
        'sentry',
        'website_odoo_debranding',
        'eb_garment'
    ],
    'data': [
        'views/product_views.xml',
        'data/general_data.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}