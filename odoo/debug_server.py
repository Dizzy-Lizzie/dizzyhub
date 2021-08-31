#!/usr/bin/python3

# set server timezone in UTC before time module imported
__import__('os').environ['TZ'] = 'UTC'



import sys, os
from urllib.parse import urlparse

import odoo

db_vars = urlparse(os.environ['DATABASE_URL'])
addons_path = os.environ['ODOO_ADDONS_PATH']

sys.argv += [
    "--addons-path={}".format(addons_path),
    "--database={}".format(os.path.basename(db_vars.path)),
    "--db_host={}".format(db_vars.hostname),
    "--db_port={}".format(db_vars.port),
    "--db_user={}".format(db_vars.username),
    "--db_password={}".format(db_vars.password),
]

if __name__ == "__main__":
    odoo.cli.main()
