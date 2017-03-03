""" Retrieve a list of managed packages installed in an org """

import base64

from xml.dom.minidom import parseString
from zipfile import ZipFile
import StringIO

from cumulusci.salesforce_api import soap_envelopes
from cumulusci.salesforce_api.metadata.base import BaseMetadataApiCall


class ApiRetrieveInstalledPackages(BaseMetadataApiCall):
    """ Callable API object that retrieves a list of installed
    packages and their version number. """

    check_interval = 1
    soap_envelope_start = soap_envelopes.RETRIEVE_INSTALLEDPACKAGE
    soap_envelope_status = soap_envelopes.CHECK_STATUS
    soap_envelope_result = soap_envelopes.CHECK_RETRIEVE_STATUS
    soap_action_start = 'retrieve'
    soap_action_status = 'checkStatus'
    soap_action_result = 'checkRetrieveStatus'

    def __init__(self, task):
        super(ApiRetrieveInstalledPackages, self).__init__(task)
        self.packages = []

    def _process_response(self, response):
        # Parse the metadata zip file from the response
        zipstr = parseString(response.content).getElementsByTagName('zipFile')
        if zipstr:
            zipstr = zipstr[0].firstChild.nodeValue
        else:
            return self.packages
        zipstringio = StringIO.StringIO(base64.b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        packages = {}
        # Loop through all files in the zip skipping anything other than
        # InstalledPackages
        for path in zipfile.namelist():
            if not path.endswith('.installedPackage'):
                continue
            namespace = path.split('/')[-1].split('.')[0]
            metadata = parseString(zipfile.open(path).read())

            version = metadata.getElementsByTagName('versionNumber')
            if version:
                version = version[0].firstChild.nodeValue
            packages[namespace] = version
        self.packages = packages
        return self.packages
