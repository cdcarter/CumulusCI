""" Retrieve metadata from an org given a package.xml """
import StringIO
import re
import base64

from xml.dom.minidom import parseString
from zipfile import ZipFile
from cumulusci.utils import zip_subfolder

from cumulusci.salesforce_api import soap_envelopes
from cumulusci.salesforce_api.metadata.base import BaseMetadataApiCall


class ApiRetrieveUnpackaged(BaseMetadataApiCall):
    """ Callable API object that retrieves the contents of a package.xml """

    check_interval = 1
    soap_envelope_start = soap_envelopes.RETRIEVE_UNPACKAGED
    soap_envelope_status = soap_envelopes.CHECK_STATUS
    soap_envelope_result = soap_envelopes.CHECK_RETRIEVE_STATUS
    soap_action_start = 'retrieve'
    soap_action_status = 'checkStatus'
    soap_action_result = 'checkRetrieveStatus'

    def __init__(self, task, package_xml, api_version):
        super(ApiRetrieveUnpackaged, self).__init__(task)
        self.package_xml = package_xml
        self.api_version = api_version
        self._clean_package_xml()

    def _clean_package_xml(self):
        self.package_xml = re.sub(r'<\?xml.*\?>', '', self.package_xml)
        self.package_xml = re.sub(r'<Package.*>', '', self.package_xml, 1)
        self.package_xml = re.sub(r'</Package>', '', self.package_xml, 1)
        self.package_xml = re.sub('\n', '', self.package_xml)
        self.package_xml = re.sub(' *', '', self.package_xml)

    def _build_envelope_start(self):
        return self.soap_envelope_start.format(
            self.api_version,
            self.package_xml,
        )

    def _process_response(self, response):
        # Pull the metadata zip out of the SOAP response
        # base64 decode it, and then open the unpackaged
        # subfolder as an in memory ZipFile
        zipstr = parseString(response.content).getElementsByTagName('zipFile')
        zipstr = zipstr[0].firstChild.nodeValue

        zipstringio = StringIO.StringIO(base64.b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')
        zipfile = zip_subfolder(zipfile, 'unpackaged')

        return zipfile
