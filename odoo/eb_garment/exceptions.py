
from odoo import exceptions


# Module scoped exceptions to ensure that errors are thrown by our
# code and not the code of other modules during testing.

class ValidationError(exceptions.ValidationError): pass

class UserError(exceptions.UserError): pass

class GarmentValueError(ValueError): pass
