""" Retrieve metadata from an org by package name """
import StringIO
import base64

from xml.dom.minidom import parseString
from zipfile import ZipFile

from cumulusci.salesforce_api import soap_envelopes
from cumulusci.salesforce_api.metadata.base import BaseMetadataApiCall


class ApiRetrievePackaged(BaseMetadataApiCall):
    """ Callable API object that retrieves the metadata of a named
    package in the org. """
    check_interval = 1
    soap_envelope_start = soap_envelopes.RETRIEVE_PACKAGED
    soap_envelope_status = soap_envelopes.CHECK_STATUS
    soap_envelope_result = soap_envelopes.CHECK_RETRIEVE_STATUS
    soap_action_start = 'retrieve'
    soap_action_status = 'checkStatus'
    soap_action_result = 'checkRetrieveStatus'

    def __init__(self, task, package_name, api_version):
        super(ApiRetrievePackaged, self).__init__(task)
        self.package_name = package_name
        self.api_version = api_version

    def _build_envelope_start(self):
        return self.soap_envelope_start.format(
            self.api_version,
            self.package_name,
        )

    def _process_response(self, response):
        # Parse the metadata zip file from the response
        zipstr = parseString(response.content).getElementsByTagName('zipFile')
        zipstr = zipstr[0].firstChild.nodeValue

        zipstringio = StringIO.StringIO(base64.b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')
        return zipfile
