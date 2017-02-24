""" Tests for the SalesforceDX Commands """

import unittest

from cumulusci.core.config import BaseGlobalConfig
from cumulusci.core.config import BaseProjectConfig
from cumulusci.core.config import OrgConfig
from cumulusci.core.config import TaskConfig
from cumulusci.tasks.salesforcedx import BaseSalesforceDXTask

class TestBaseSalesforceDXTask(unittest.TestCase):
    """ Test the base salesforce dx tast """

    def setUp(self):
        self.global_config = BaseGlobalConfig()
        self.project_config = BaseProjectConfig(self.global_config)
        self.org_config = OrgConfig({
            'username': 'sample@example',
            'org_id': '00D000000000001'
        })
        self.task_config = TaskConfig()

    def test_task_is_callable(self):
        """ BaseTask is Callable """
        task = BaseSalesforceDXTask(
            self.project_config,
            self.task_config,
            self.org_config
        )
        task()

        self.fail('Finish the test!')

