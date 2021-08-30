{
    'name': 'Garment Product Type',
    'version': '0.1',
    'summary': 'Garment Product Type',
    'sequence': 10,
    'description': """Garment Product Type""",
    'category': 'Tools',
    'website': 'https://github.com/etherealite',
    'depends': [
        'product', 'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/garment_data.xml',
        'views/garment_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': True,
}