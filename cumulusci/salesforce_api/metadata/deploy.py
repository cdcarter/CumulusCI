""" Deploy metadata to a Salesforce org """

from xml.dom.minidom import parseString

from cumulusci.salesforce_api.exceptions import MetadataComponentFailure
from cumulusci.salesforce_api.exceptions import MetadataApiError
from cumulusci.salesforce_api import soap_envelopes
from cumulusci.salesforce_api.metadata.base import BaseMetadataApiCall

def reach(nodelist):
    """ Reach into the first node value """
    return nodelist[0].firstChild.nodeValue

class ApiDeploy(BaseMetadataApiCall):
    """ Callable API object that deploys a zipfile package to an org. """

    soap_envelope_start = soap_envelopes.DEPLOY
    soap_envelope_status = soap_envelopes.CHECK_DEPLOY_STATUS
    soap_action_start = 'deploy'
    soap_action_status = 'checkDeployStatus'

    def __init__(self, task, package_zip, purge_on_delete=None):
        super(ApiDeploy, self).__init__(task)
        if purge_on_delete is None:
            purge_on_delete = True
        self._set_purge_on_delete(purge_on_delete)
        self.package_zip = package_zip

    def _set_purge_on_delete(self, purge_on_delete):
        if not purge_on_delete or purge_on_delete == 'false':
            self.purge_on_delete = 'false'
        else:
            self.purge_on_delete = 'true'

    def _build_envelope_start(self):
        if self.package_zip:
            return self.soap_envelope_start % {
                'package_zip': self.package_zip,
                'purge_on_delete': self.purge_on_delete,
            }

    def _process_response(self, response):
        status = parseString(response.content).getElementsByTagName('status')
        if status:
            status = reach(status)
        else:
            # If no status element is in the result xml, return fail and log
            # the entire SOAP envelope in the log
            self._set_status('Failed', response.content)
            return self.status
        # Only done responses should be passed so we need to handle any status
        # related to done
        if status in ['Succeeded', 'SucceededPartial']:
            self._set_status('Success', status)
        else:
            # parse out the failue text and raise appropriate exception
            messages = []
            resp_xml = parseString(response.content)

            component_failures = resp_xml.getElementsByTagName(
                'componentFailures')
            for component_failure in component_failures:
                failure_info = {
                    'component_type': None,
                    'file_name': None,
                    'line_num': None,
                    'column_num': None,
                    'problem': reach(
                        component_failure.getElementsByTagName('problem')
                    ),
                    'problem_type': reach(
                        component_failure.getElementsByTagName('problemType')
                    ),
                }
                component_type = component_failure.getElementsByTagName(
                    'componentType')
                if component_type and component_type[0].firstChild:
                    failure_info['component_type'] = reach(component_type)
                file_name = component_failure.getElementsByTagName('fullName')
                if file_name and file_name[0].firstChild:
                    failure_info['file_name'] = reach(file_name)
                if not failure_info['file_name']:
                    file_name = component_failure.getElementsByTagName(
                        'fileName'
                    )
                    if file_name and file_name[0].firstChild:
                        failure_info['file_name'] = reach(file_name)

                line_num = component_failure.getElementsByTagName('lineNumber')
                if line_num and line_num[0].firstChild:
                    failure_info['line_num'] = reach(line_num)

                column_num = component_failure.getElementsByTagName(
                    'columnNumber')
                if column_num and column_num[0].firstChild:
                    failure_info['column_num'] = reach(column_num)

                created = component_failure.getElementsByTagName(
                    'created')[0].firstChild.nodeValue == 'true'
                deleted = component_failure.getElementsByTagName(
                    'deleted')[0].firstChild.nodeValue == 'true'
                if deleted:
                    failure_info['action'] = 'Delete'
                elif created:
                    failure_info['action'] = 'Create'
                else:
                    failure_info['action'] = 'Update'

                if failure_info['file_name'] and failure_info['line_num']:
                    messages.append(
                        '{action} of {component_type} {file_name}: {problem_type} on line {line_num}, col {column_num}: {problem}'.format(
                            **failure_info))
                elif failure_info['file_name']:
                    messages.append(
                        '{action} of {component_type} {file_name}: {problem_type}: {problem}'.format(
                            **failure_info))
                else:
                    messages.append(
                        '{action} of {problem_type}: {problem}'.format(
                            **failure_info))

            if messages:
                # Deploy failures due to a component failure should raise
                # MetadataComponentFailure
                log = '\n\n'.join(messages)
                self._set_status('Failed', log)
                raise MetadataComponentFailure(log, response)

            else:
                problems = parseString(
                    response.content).getElementsByTagName('problem')
                for problem in problems:
                    messages.append(problem.firstChild.nodeValue)

            # Parse out any failure text (from test failures in production
            # deployments) and add to log
            failures = parseString(
                response.content).getElementsByTagName('failures')
            for failure in failures:
                # Get needed values from subelements
                namespace = failure.getElementsByTagName('namespace')
                if namespace and namespace[0].firstChild:
                    namespace = reach(namespace)
                else:
                    namespace = None
                stacktrace = failure.getElementsByTagName('stackTrace')
                if stacktrace and stacktrace[0].firstChild:
                    stacktrace = reach(stacktrace)
                else:
                    stacktrace = None
                message = ['Apex Test Failure: ', ]
                if namespace:
                    message.append('from namespace %s: ' % namespace)
                if stacktrace:
                    message.append(stacktrace)
                messages.append(''.join(message))
            if messages:
                log = '\n\n'.join(messages)
            else:
                log = response.content

            if messages:
                # Deploy failures due to a component failure should raise
                # MetadataComponentFailure
                log = '\n\n'.join(messages)
                self._set_status('Failed', log)
                raise ApexTestException(log)

            self._set_status('Failed', log)
            raise MetadataApiError(log, response)

        return self.status
