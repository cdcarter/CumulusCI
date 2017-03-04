""" List metadata """

from xml.dom.minidom import parseString


from cumulusci.salesforce_api import soap_envelopes
from cumulusci.salesforce_api.metadata.base import BaseMetadataApiCall


class ApiListMetadata(BaseMetadataApiCall):
    """ Callable API class for listing metadata of a type. """
    soap_envelope_start = soap_envelopes.LIST_METADATA
    soap_action_start = 'listMetadata'

    def __init__(self, task, metadata_type, metadata=None, folder=None):
        super(ApiListMetadata, self).__init__(task)
        self.metadata_type = metadata_type
        self.metadata = metadata
        self.folder = folder
        if self.metadata is None:
            self.metadata = {}

    def _build_envelope_start(self):
        folder = self.folder
        if folder is None:
            folder = ''
        return self.soap_envelope_start % {
            'metadata_type': self.metadata_type,
            'folder': self.folder}

    def _process_response(self, response):
        metadata = []
        tags = [
            'createdById',
            'createdByName',
            'createdDate',
            'fileName',
            'fullName',
            'id',
            'lastModifiedById',
            'lastModifiedByName',
            'lastModifiedDate',
            'manageableState',
            'namespacePrefix',
            'type',
        ]
        # These tags will be interpreted into dates
        # parse_dates = [
        #    'createdDate',
        #    'lastModifiedDate',
        # ]
        for result in parseString(
                response.content).getElementsByTagName('result'):
            result_data = {}
            # Parse fields
            for tag in tags:
                result_data[tag] = self._get_element_value(result, tag)
            # Parse dates
            # : This was breaking things
            # for key in parse_dates:
            #    if result_data[key]:
            #        result_data[key] = dateutil.parser.parse(result_data[key])
            metadata.append(result_data)
        if self.metadata_type in self.metadata:
            self.metadata[self.metadata_type].extend(metadata)
        else:
            self.metadata[self.metadata_type] = metadata
        return self.metadata
