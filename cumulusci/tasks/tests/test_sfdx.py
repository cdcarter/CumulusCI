""" Tests for the SalesforceDX Commands """

import unittest

from cumulusci.core.config import BaseGlobalConfig
from cumulusci.core.config import BaseProjectConfig
from cumulusci.core.config import OrgConfig
from cumulusci.core.config import TaskConfig

from cumulusci.tasks.sfdx import BaseSFDXTask
from cumulusci.tasks.sfdx import SFDXScratchOrgTask
from cumulusci.tasks.sfdx import SFDXKeychainOrgTask


class BaseSFDXTests(unittest.TestCase):
    """ Tests for BaseSFDXTask """

    def setUp(self):
        self.global_config = BaseGlobalConfig()
        self.project_config = BaseProjectConfig(self.global_config)
        self.task_config = TaskConfig()
        self.org_config = OrgConfig({
            'username': 'sample@example',
            'org_id': '00D000000000001',
            'instance_url': 'https://null.my.salesforce.com',
            'access_token': '00D000000000001!fhdjalfhdjlkahfdjklahfjldsha'
        })

    def test_call_command_without_org(self):
        """ When calling an sfdx command without an org,
        no username is passed """
        self.task_config.config['options'] = {'command': 'force:org:open'}
        task = BaseSFDXTask(self.project_config, self.task_config)
        self.assertNotIn('-u ', task.full_command)
        self.assertNotIn('--targetusername', task.full_command)

    def test_command_from_options(self):
        """ SFDX shells out to the command supplied in task options """
        self.task_config.config['options'] = {'command': 'force:org:open'}
        task = BaseSFDXTask(self.project_config, self.task_config)

        self.assertEqual('sfdx force:org:open', task.full_command)

    def test_command_with_options(self):
        """ SFDX adds options to the command line """
        self.task_config.config['options'] = {
            'command': 'force:schema:sobject:list',
            'options': '-t all'
        }

        task = BaseSFDXTask(self.project_config, self.task_config)
        self.assertIn('-t all', task.full_command)


class Functionaltests(BaseSFDXTests):
    """ Broad functional tests for the sfdx commands """

    def test_call_command_with_scratch_org(self):
        """ When calling an sfdx command with a scratch org, the username
        is passed as a command line argument.
        """
        self.task_config.config['options'] = {'command': 'force:org:open'}
        task = SFDXScratchOrgTask(self.project_config, self.task_config,
                                  self.org_config)
        self.assertIn('--targetusername', task.full_command)
        self.assertIn(
            self.org_config.config['username'],
            task.full_command
        )

    def test_call_command_with_keychain_org(self):
        """ When calling an sfdx command with a cci keychain org, the
        instanceUrl is passed as an env var, and the access token is passed
        as a command line argument. """
        task_config = TaskConfig({'command': 'force:org:open'})
        task = SFDXKeychainOrgTask(self.project_config, task_config,
                                   self.org_config)
        self.assertIn('--targetusername', task.full_command)
        self.assertIn(
            self.org_config.config['access_token'],
            task.full_command
        )
