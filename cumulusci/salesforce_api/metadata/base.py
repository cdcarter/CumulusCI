
import base64
import httplib
import re
import time
from xml.dom.minidom import parseString
from zipfile import ZipFile
import StringIO

import requests

from cumulusci.salesforce_api import soap_envelopes
from cumulusci.core.exceptions import ApexTestException
from cumulusci.utils import zip_subfolder
from cumulusci.salesforce_api.exceptions import MetadataComponentFailure
from cumulusci.salesforce_api.exceptions import MetadataApiError


class BaseMetadataApiCall(object):
    check_interval = 1
    soap_envelope_start = None
    soap_envelope_status = None
    soap_envelope_result = None
    soap_action_start = None
    soap_action_status = None
    soap_action_result = None

    def __init__(self, task):
        # the cumulucci context object contains logger, oauth, ID, secret, etc
        self.task = task
        self.status = None
        self.check_num = 1

    def __call__(self):
        self.task.logger.info('Pending')
        response = self._get_response()
        if self.status != 'Failed':
            return self._process_response(response)

    def _build_endpoint_url(self):
        # Parse org id from id which ends in /ORGID/USERID
        org_id = self.task.org_config.org_id
        # If "My Domain" is configured in the org, the instance_url needs to be
        # parsed differently
        instance_url = self.task.org_config.instance_url
        if instance_url.find('.my.salesforce.com') != -1:
            # Parse instance_url with My Domain configured
            # URL will be in the format
            # https://name--name.na11.my.salesforce.com and should be
            # https://na11.salesforce.com
            instance_url = re.sub(
                r'https://.*\.(\w+)\.my\.salesforce\.com',
                r'https://\1.salesforce.com',
                instance_url)
        # Build the endpoint url from the instance_url
        endpoint = '%s/services/Soap/m/33.0/%s' % (instance_url, org_id)
        return endpoint

    def _build_envelope_result(self):
        if self.soap_envelope_result:
            return self.soap_envelope_result % {'process_id': self.process_id}

    def _build_envelope_start(self):
        if self.soap_envelope_start:
            return self.soap_envelope_start

    def _build_envelope_status(self):
        if self.soap_envelope_status:
            return self.soap_envelope_status % {'process_id': self.process_id}

    def _build_headers(self, action, message):
        return {
            'Content-Type': 'text/xml; charset=UTF-8',
            'Content-Length': str(len(message)),
            'SOAPAction': action,
        }

    def _call_mdapi(self, headers, envelope, refresh=None):
        # Insert the session id
        session_id = self.task.org_config.access_token
        auth_envelope = envelope.replace('###SESSION_ID###', session_id)
        response = requests.post(self._build_endpoint_url(
        ), headers=headers, data=auth_envelope)
        faultcode = parseString(
            response.content).getElementsByTagName('faultcode')
        # refresh = False can be passed to prevent a loop if refresh fails
        if refresh is None:
            refresh = True
        if faultcode:
            return self._handle_soap_error(
                headers, envelope, refresh, response)
        return response

    def _get_element_value(self, dom, tag):
        result = dom.getElementsByTagName(tag)
        if result and result[0].firstChild:
            return result[0].firstChild.nodeValue

    def _get_check_interval(self):
        return self.check_interval * ((self.check_num / 3) + 1)

    def _get_response(self):
        # Start the call
        envelope = self._build_envelope_start()
        if not envelope:
            return
        envelope = envelope.encode('utf-8')
        headers = self._build_headers(self.soap_action_start, envelope)
        response = self._call_mdapi(headers, envelope)
        # If no status or result calls are configured, return the result
        if not self.soap_envelope_status and not self.soap_envelope_result:
            return response
        # Process the response to set self.process_id with the process id
        # started
        response = self._process_response_start(response)
        # Check the status if configured
        if self.soap_envelope_status:
            while self.status not in ['Done', 'Failed']:
                # Check status in a loop until done
                envelope = self._build_envelope_status()
                if not envelope:
                    return
                envelope = envelope.encode('utf-8')
                headers = self._build_headers(
                    self.soap_action_status, envelope)
                response = self._call_mdapi(headers, envelope)
                response = self._process_response_status(response)

                # start increasing the check interval progressively to handle
                # long pending jobs
                check_interval = self._get_check_interval()
                self.check_num += 1

                time.sleep(check_interval)
            # Fetch the final result and return
            if self.soap_envelope_result:
                envelope = self._build_envelope_result()
                if not envelope:
                    return
                envelope = envelope.encode('utf-8')
                headers = self._build_headers(
                    self.soap_action_result, envelope)
                response = self._call_mdapi(headers, envelope)
            else:
                return response
        else:
            # Check the result and return when done
            while self.status not in ['Succeeded', 'Failed', 'Cancelled']:
                # start increasing the check interval progressively to handle
                # long pending jobs
                check_interval = self._get_check_interval()
                self.check_num += 1
                time.sleep(check_interval)

                envelope = self._build_envelope_result()
                envelope = envelope.encode('utf-8')
                headers = self._build_headers(
                    self.soap_action_result, envelope)
                response = self._call_mdapi(headers, envelope)
                response = self._process_response_result(response)
        return response

    def _handle_soap_error(self, headers, envelope, refresh, response):
        faultcode = parseString(
            response.content).getElementsByTagName('faultcode')
        if faultcode:
            faultcode = faultcode[0].firstChild.nodeValue
        else:
            faultcode = ''
        faultstring = parseString(
            response.content).getElementsByTagName('faultstring')
        if faultstring:
            faultstring = faultstring[0].firstChild.nodeValue
        else:
            faultstring = response.content
        if (faultcode == 'sf:INVALID_SESSION_ID' and
                self.task.org_config and
                self.task.org_config.refresh_token):
            # Attempt to refresh token and recall request
            if refresh:
                self.task.org_config.refresh_oauth_token()
                return self._call_mdapi(headers, envelope, refresh=False)
        # Log the error
        message = '{}: {}'.format(faultcode, faultstring)
        self._set_status('Failed', message)
        raise MetadataApiError(message, response)

    def _process_response(self, response):
        return response

    def _process_response_result(self, response):
        self._set_status('Succeeded')
        return response

    def _process_response_start(self, response):
        if response.status_code == httplib.INTERNAL_SERVER_ERROR:
            return response
        ids = parseString(response.content).getElementsByTagName('id')
        if ids:
            self.process_id = ids[0].firstChild.nodeValue
        return response

    def _process_response_status(self, response):
        resp_xml = parseString(response.content)
        done = resp_xml.getElementsByTagName('done')
        if done:
            if done[0].firstChild.nodeValue == 'true':
                self._set_status('Done')
            else:
                state_detail = resp_xml.getElementsByTagName('stateDetail')
                if state_detail:
                    log = state_detail[0].firstChild.nodeValue
                    self._set_status('InProgress', log)
                    self.check_num = 1
                elif self.status == 'InProgress':
                    self.check_num = 1
                    self._set_status(
                        'InProgress', 'next check in {} seconds'.format(
                            self._get_check_interval()))
                else:
                    self._set_status(
                        'Pending', 'next check in {} seconds'.format(
                            self._get_check_interval()))
        else:
            # If no done element was in the xml, fail logging the entire SOAP
            # envelope as the log
            self._set_status('Failed', response.content)
        return response

    def _set_status(self, status, log=None, level=None):
        if not level:
            level = 'info'
            if status == 'Failed':
                level = 'error'
        logger = getattr(self.task.logger, level)
        self.status = status
        if log:
            logger('[{}]: {}'.format(status, log))
        else:
            logger('[{}]'.format(status))
