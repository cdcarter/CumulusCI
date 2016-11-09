from cumulusci.core.tasks import BaseTask

import sarge

class BaseSargeTask(BaseTask):
    name = 'BaseSargeTask'

    def _run_task(self):
        raise NotImplementedError(
            'Subclasses should provide their own implementation')

    def _init_task(self):
        self.sarge = self._get_api()

    def _get_api(self):
        return sarge

