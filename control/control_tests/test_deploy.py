import os

from unittest import mock
from unittest.mock import MagicMock, patch

import control

from control import Operator
from control import FlyCtl




os.environ['FLY_ACCESS_TOKEN'] = ''

@patch.object(control.FlyCtl, 'app_destroy')
def test_mock_method(mock_app_destroy):

    fake_val = 'app destroyed'
    mock_app_destroy.return_value = fake_val

    flyctl = control.FlyCtl()


    assert flyctl.app_destroy(['sfljl']) == fake_val

def test_mock_class():
    mock_flyctl = mock.create_autospec(control.FlyCtl)
    mock_flyctl.app_destroy.return_value = '123'

    assert mock_flyctl.app_destroy(['sdflkj']) == '123'

def test_init_app():
    mock_flyctl = mock.create_autospec(FlyCtl)
    operator = Operator(mock_flyctl, '/fake/path')

    app_instance_name = 'mock-app-name'
    org_name = 'mock-org-name'

    operator.init_app(app_instance_name, org_name)

    mock_flyctl.init.assert_called_with([
        app_instance_name,
        '--import', os.path.join('fake/path', app_instance_name, 'fly.toml'),
        '--org', org_name,
        '--nowrite',
    ])