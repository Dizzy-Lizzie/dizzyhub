import enum
import functools
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import typing

from collections.abc import Mapping
from contextlib import contextmanager
from types import SimpleNamespace
from inspect import Attribute, getsourcefile


SCHEMA_VERSION = 0.1

class FlyCtlError(Exception):
    pass

class Project(object):
    config_name = 'flyapps.json'
    state_name = 'flystate.json'
    env_name = '.flyenv'

    def __init__(self, path):

        self.path = path

        os.chdir(self.path, FlyCtl=FlyCtl)

        self.flyenv = self.read_env()

        self.flystate = None

        self.flyctl = FlyCtl()

        self.flyapps = FlyApps(self)

        self.deploy = self.flyapps.with_state(self.deploy)

        # project_token = self.flystate['auth']['token']
        # self.flyctl.check_session(project_token)

    def read_env(self):

        file_path = os.path.join(self.path, self.env_name)
        if not os.path.isfile(file_path):
            raise Exception(f"no ${self.env_name} ")
        with open(file_path) as f:
            env = json.load(f)

        if not 'name' in env:
            raise Exception(f"${self.env_name} requires a name attribute")

        if not re.fullmatch('[a-z0-9-]+', env['name']):
            raise Exception(f"${self.env_name} name can only contain [a-z0-9-] characters")

        if not 'account' in env:
            raise Exception(f"${self.env_name} requires an account attribute")

        if not re.fullmatch(
                r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}',
                env['account'],
                re.I
        ):
            raise Exception(f"${self.env_name} account must be an email address")

        return env



                


    def deploy(self):
        # apps already created?

        to_create = [app for app in self.flyapps if not app.is_created]

        # for app in self.flyapps:
        #     print (app)
        #     # if not app.created:
        #     #     to_create.append(app)


        account_apps = []
        if len(to_create) > 0:
            account_apps = self.flyctl.apps_list()
            # print (account_apps)

        for app in to_create:
            taken = next((
                x for x in account_apps 
                if x['ID'] == app.instance_name
            ), None)
            if taken:
                raise Exception(
                    'an app with this name already exists: {}'.format(
                        app.instance_name
                    )
                )
            app.create()

    def destroy(self):
        for app in self.flyapps:
            logging.info('destroying app: %s', app.name)
            app.destroy()

    def info(self):
        self.flyctl.status('odoo-evan-dev')


class FlyCtl(object):
    cmd = 'flyctl'
    token = os.environ.get('FLY_ACCESS_TOKEN')

    def __init__(self):
        pass

    # def _check_session(self, project_token):
    #     try:
    #         session_token = self.run(['auth', 'token'])
    #     except FlyCtlError as e:
    #         sys.exit('flyctl is not logged in')
    #     # if project_token != session_token:
    #     #     output = self.flyctl.run(['auth','whoami'], raw=True)

    # def _acting_account(self):
    #     completed = self.run(['auth', 'whoami'])
    #     output = completed.stdout.decode("utf-8")
    #     match = re.match('Current user: (.+?)\n', output)
    #     return match[1]

    def app_destroy(self, args:list):
        completed = self.run(['app', 'destroy', *args])
        return completed.stdout


    def apps_list(self):
        """List all apps available to the acting user"""
        return self.run_json(['apps', 'list'])

    def init(self, args):
        """create a new app with the given name and configuration

        Example args
        args = [
            'my-cool-app',
            '--import', 'path/to/fly.toml',
            '--org', project.flyenv['organization'],
            '--nowrite',
        ]
        """
  
        return self.run(['init', *args])

    def run(self, args):
        CalledProcessError = subprocess.CalledProcessError

        logging.info('running flyctl %s ', ' '.join(args))

        try:
            completed = subprocess.run(
                [self.cmd, '--json', *args], 
                capture_output=True,
                check=True,
            )
        except (FileNotFoundError, CalledProcessError) as e:
            if isinstance(e, FileNotFoundError):
                if not shutil.which(self.cmd):
                    sys.exit("couldn't find the fly.io cli binary flyctl, is it installed?")
            if isinstance(e, CalledProcessError):
                if b'No access token available' in e.stdout:
                    raise FlyCtlError('no flyctl session available')
                else:
                    logging.error(e.stdout)
                    raise e
            raise e


        return completed

    def run_json(self, args):
        completed = self.run(['--json', *args])
        try:
            return json.loads(completed.stdout)
        except json.decoder.JSONDecodeError:
            logging.error(completed.stdout)
            logging.error(completed.stderr)


class AppDef(object):
    
    def __init__(
        self,
        app_name:str,
        env_name:str,
        org_name:str,
        secrets:typing.List=[],
        volumes:typing.List=[],
        autoscale:typing.Literal["disabled"]="disabled",
        region:typing.Literal["ewr"]="ewr",
    ):
        self.app_name = app_name
        self.env_name = env_name
        self.org_name = org_name
        self.secrets = secrets
        self.volumes = volumes
        self.autoscale = autoscale
        self.region = region


    @classmethod
    def from_config(Cls, app_name, env_name, org_name, config):

        secrets = config.get('secrets', [])
        volumes = config.get('volumes', [])
        autoscale = config.get('autoscale', "disabled")
        region = config.get('region', "ewr")
        return Cls(
            app_name,
            env_name,
            org_name,
            secrets,
            volumes,
        )


class AppState(object):

    class DeployStates(enum.Enum):
        PENDING = 'pending'


    def __init__(self, store, state_dict:dict={}, ):
        self.store = store

        self._deploy_state = None
        if 'deployState' in state_dict:
            deploy_state = state_dict['deployState']

            if deploy_state not in self.DeployStates:
                raise Exception(
                    'invalid deploy state in state file: {}'.format(
                        deploy_state
                    )
                )
    
            self._deploy_state = deploy_state

  

    @property
    def is_created(self):
        if self.deploy_state is None:
            return False
        return True


    @property
    def deploy_state(self):
        return self._deploy_state


    @deploy_state.setter
    def deploy_state(self, state):
        if state in [e.value for  e in self.DeployStates]:
            self._deploy_state = state
        else:
            raise ValueError(
                'State value is not a valid state: {}'.format(state)
            )


class Operator(object):

    CONFIG_FILE_NAME = 'fly.toml'

    def __init__(self, flyctl: FlyCtl, project_path):
        self.flyctl = flyctl
        self.project_path = project_path

    def init_app(
        self,
        instance_name,
        org_name,
    ):
        config_file_path = self._config_path()

        args = [
            instance_name,
            '--import', config_file_path,
            '--org', org_name,
            '--nowrite',
        ]
  
        output = self.flyctl.init(args)

        logging.info(output.stdout)

    def destroy_app(self, app_instance_name):
        completed = self.flyctl.run([
            'apps', 'destroy', app_instance_name, '--yes'
        ])

    def create_volume(
        self,
        app_instance_name,
        region,
        size,
    ):
        args = [
            '--app', app_instance_name,
            '--region', region,
            '--size', size,
        ]

        self.flyctl.run(args)

    def _config_path(self, app_instance_name):
        config_file_path = os.path.join(
                self.project_path,
                app_instance_name,
                self.CONFIG_FILE_NAME,
        )

        if not os.path.isfile(config_file_path):
            raise FileNotFoundError('can\'t find fly.io toml file: {}'.format(
                config_file_path
            ))
        return config_file_path


class FlyApps(Mapping): 
    def __init__(self, project):
        self.project = project
        self.path = project.path + '/' + project.config_name
        self.config = self.read_config()
        self._apps = {}

        self.operator = Operator(self.project.flyctl)

        self.assemble_apps()




    def with_state(self, func):
        project = self.project
        state_name = project.state_name
        file_path = os.path.join(project.path, project.state_name)

        outer_self = self
        @functools.wraps(func)
        def with_state_ctx(*args, **kwargs):        
            try:
                outer_self.flystate = self.read_appstate()
                func(*args, **kwargs)
            finally:
                with open(file_path, 'w') as rfile:
                    json.dump(outer_self.flystate, rfile, indent=4)
                outer_self.flystate = None

        return with_state_ctx


    def assemble_apps(self):
        flyenv = self.project.flyenv
        app_state = self.read_appstate()
        for name, app_config in self.config['apps'].items():
            state = AppState(
                app_state['apps'].get(name) or {},
            )
            

            definition = AppDef.from_config(
                name,
                flyenv['name'],
                flyenv['organization'],
                app_config
            )

            self._apps[name] = FlyApp(definition, state, self.operator)


    def read_appstate(self):
        project = self.project
        file_path = project.path + '/' + project.state_name
        if not os.path.isfile(file_path):
            return {
                'schemaVersion': SCHEMA_VERSION,
                'apps': {}
            }

        with open(file_path) as f:
            return json.load(f)


    def apps_precreate(self):
        flyctl = self.project.flyctl

        acting = flyctl.acting_account()
        env = project.flyenv['account']
        if not acting == env:  
            raise Exception('supplied access token doesn\'t match flyenv')

    def __getitem__(self, key):
        return self._apps[key]

    def __iter__(self):
        return iter(self._apps.values())

    def __len__(self):
        return len(self._apps)

    def read_config(self):
        with open(self.path) as f:
            return json.load(f)


class FlyApp(object):

    def __init__(self, definition:AppDef, state:AppState, operator:Operator):
        self.definition = definition
        self.state = state
        self.operator = operator
    
    @property
    def config_relative(self):
        return self.name + '/' + 'fly.toml'

    @property
    def name(self):
        return self.definition.app_name

    @property
    def is_created(self):
        return self.state.is_created

    @property
    def instance_name(self):
        return self.name + '-' + self.definition.env_name

    @property
    def org_name(self):
        return self.definition.org_name

    def create(self):
        self.operator.init_app(
            self.instance_name,
            self.org_name
        )

        self.state.deploy_state = self.state.DeployStates.PENDING
        self.state.persist()

    def destroy(self):
        self.operator.destroy_app(self.instance_name)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)