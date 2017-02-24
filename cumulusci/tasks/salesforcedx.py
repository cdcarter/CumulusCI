""" Tasks for using the SalesforceDX CLI tool

BaseSalesforceDXTask allows you to call the sfdx binary with options
CumulusCIOrgDXTask shells out with credentials from a keychain org """

import sarge

from cumulusci.core.exceptions import SalesforceDXException
from cumulusci.core.tasks import BaseTask


class BaseSalesforceDXTask(BaseTask):
    """ A SalesforceDX task uses Sarge to shell out to the sfdx binary """
    task_options = {
        'command': {
            'description':
                'The sfdx command to call. For example: force:src:push',
            'required': True,
        },
        'options': {
            'description': 'The command line options to pass to the command',
        },
    }

    def _call_salesforce_dx(self, command, options=None):
        full_command = 'sfdx ' + command
        if options:
            full_command += ' {}'.format(options)

        full_command += ' -u {}'.format(self.org_config.username)

        self.logger.info('Running: %s', full_command)
        p = sarge.Command(full_command, stdout=sarge.Capture(buffer_size=-1))
        p.run()

        for line in p.stdout:  # pylint: disable=E1101
            self.logger.info(line)

        if p.returncode:
            message = '{}: {}'.format(
                p.returncode,
                p.stdout  # pylint: disable=E1101
            )

            self.logger.error(message)
            raise SalesforceDXException(message)

    def _run_task(self):
        self._call_salesforce_dx(
            self.options['command'],
            self.options.get('options')
        )


class CumulusCIOrgDXTask(BaseSalesforceDXTask):
    """A task that shells out to SFDX with credentials from a keychain org. """

    salesforce_task = True

    def _run_task(self):
        self._call_salesforce_dx(
            'force:config:set',
            {'instanceUrl={}'.format(self.org_config.instance_url)}
        )
        self._call_salesforce_dx(
            self.options['command'],
            '{} --target-username {}'.format(
                self.options.get('options'),
                self.org_config.username
            )
        )
