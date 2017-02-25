""" Tasks for using the SFDX CLI tool

BaseSFDXTask allows you to call the sfdx binary with options """

import sarge

from cumulusci.core.tasks import BaseTask


class BaseSFDXTask(BaseTask):
    """ Use sarge to call the sfdx command line interface. """

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

    @property
    def full_command(self):
        """ The full command that will be run by Sarge """

        args = [self.options['command']]
        format_str = 'sfdx {0}'
        if 'options' in self.options:
            args.append(self.options['options'])
            format_str += ' {1}'

        return sarge.shell_format(format_str, *args)


class SFDXScratchOrgTask(BaseSFDXTask):
    """ Use sarge to call the sfdx command line interface. """
    pass


class SFDXKeychainOrgTask(BaseSFDXTask):
    """ Use sarge to call the sfdx command line interface. """
    pass
