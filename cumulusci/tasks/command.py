""" Tasks for running shell commands (using subprocess).

Tasks::
    Command: Run a shell command with environment variables.
    SalesforceCommand: Run a shell command with Salesforce credentials.
    SalesforceBrowserTest: Run a browser test locally or on Saucelabs.

"""

import json
import os
import subprocess

from cumulusci.core.exceptions import CommandException
from cumulusci.core.tasks import BaseTask


class Command(BaseTask):
    """ Run a shell command from a directory with environment variables.

    Using `subprocess`, Command runs a shell task, and optionally passes
    environment variables from the calling context or from task_options."""
    task_options = {
        'command': {
            'description': 'The command to execute',
            'required': True,
        },
        'dir': {
            'description': 'The directory the command should be run from. '
                           'Defaults to the current working directory.',
        },
        'env': {
            'description': 'Environment variables to set for command. '
                           'Must be flat dict, either as python dict from '
                           'YAML or as JSON string.',
        },
        'pass_env': {
            'description': 'If False, the current environment variables won\'t'
                           ' be passed to the child process. Defaults to True',
            'required': True,
        },
    }

    def _init_options(self, kwargs):
        super(Command, self)._init_options(kwargs)
        if 'pass_env' not in self.options:
            self.options['pass_env'] = True
        if self.options['pass_env'] == 'False':
            self.options['pass_env'] = False
        if 'dir' not in self.options or not self.options['dir']:
            self.options['dir'] = '.'
        if 'env' not in self.options:
            self.options['env'] = {}
        else:
            try:
                self.options['env'] = json.loads(self.options['env'])
            except TypeError:
                # assume env is already dict
                pass

    def _run_task(self):
        env = self._get_env()
        self._run_command(env)

    def _get_env(self):
        if self.options['pass_env']:
            env = os.environ.copy()
        else:
            env = {}

        env.update(self.options['env'])
        return env

    def _process_output(self, line):
        self.logger.info(line.rstrip())

    def _handle_returncode(self, process):
        if process.returncode:
            message = 'Return code: {}\nstderr: {}'.format(
                process.returncode,
                process.stderr,
            )
            self.logger.error(message)
            raise CommandException(message)

    def _run_command(self, env):
        shell_process = subprocess.Popen(
            self.options['command'],
            stdout=subprocess.PIPE,
            bufsize=1,
            shell=True,
            executable='/bin/bash',
            env=env,
            cwd=self.options.get('dir'),
        )
        for line in iter(shell_process.stdout.readline, ''):
            self._process_output(line)
        shell_process.stdout.close()
        shell_process.wait()
        self._handle_returncode(shell_process)


class SalesforceCommand(Command):
    """ Run a command with SF_ACCESS_TOKEN and SF_INSTANCE_URL on the environment.

    Automatically refreshes the access token for the selected organization and
    sets SF_ACCESS_TOKEN and SF_INSTANCE_URL as environment variables before
    running the shell command. """
    salesforce_task = True

    def _update_credentials(self):
        self.org_config.refresh_oauth_token(
            self.project_config.keychain.get_connected_app()
        )

    def _get_env(self):
        env = super(SalesforceCommand, self)._get_env()
        env['SF_ACCESS_TOKEN'] = self.org_config.access_token
        env['SF_INSTANCE_URL'] = self.org_config.instance_url
        return env


class SalesforceBrowserTest(SalesforceCommand):
    """ Runs a shell command that executes a browser test.

    SalesforceBrowserTest provides a wrapper around a SalesforceCommand
    task that allos the command to be run either locally or remotely on
    Saucelabs. This means the same task definition can be used in a developer
    flow and in a CI flow, running the same task in different locations.

    If the use_saucelabs task option is configured, the following additional
    variables are put into the environment:
        SAUCE_NAME: the username configured in the saucelabs service
        SAUCE_KEY: the api key configured in the saucelabs service
        RUN_ON_SAUCE: always set to True

    """

    task_options = Command.task_options.copy()
    task_options['use_saucelabs'] = {
        'description': 'If True, use SauceLabs to run the tests.  The '
                       'SauceLabs credentials will be fetched from the '
                       'saucelabs service in the keychain and passed as '
                       'environment variables to the command. '
                       'Defaults to False to run tests in the local browser.',
        'required': True,
    }

    def _init_options(self, kwargs):
        super(SalesforceBrowserTest, self)._init_options(kwargs)
        if ('use_saucelabs' not in self.options or
                self.options['use_saucelabs'] == 'False'):
            self.options['use_saucelabs'] = False

    def _get_env(self):
        env = super(SalesforceBrowserTest, self)._get_env()
        if self.options['use_saucelabs']:
            saucelabs = self.project_config.keychain.get_service('saucelabs')
            env['SAUCE_NAME'] = saucelabs.username
            env['SAUCE_KEY'] = saucelabs.api_key
            env['RUN_ON_SAUCE'] = 'True'
        else:
            env['RUN_LOCAL'] = 'True'
        return env
