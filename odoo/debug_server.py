#!/usr/bin/python3

# set server timezone in UTC before time module imported
__import__('os').environ['TZ'] = 'UTC'

from lxml import etree

import odoo.tools.convert as convert
from odoo.tools.convert import (
    nodeattr2bool, ParseError
)


def _tag_root(self, el):
    for rec in el:
        f = self._tags.get(rec.tag)
        if f is None:
            continue

        self.envs.append(self.get_env(el))
        self._noupdate.append(nodeattr2bool(el, 'noupdate', self.noupdate))
        try:
            f(rec)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError('while parsing %s:%s, near\n%s' % (
                rec.getroottree().docinfo.URL,
                rec.sourceline,
                etree.tostring(rec, encoding='unicode').rstrip()
            )) from e
        finally:
            self._noupdate.pop()
            self.envs.pop()

convert.xml_import._tag_root = _tag_root

import odoo

if __name__ == "__main__":
    odoo.cli.main()
