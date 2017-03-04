""" The MDAPI Implementation

Okay, where to start. Splitting out the metadata.py file out into a module,
one that may then hoist out base? I dunno. still. Wanna get these into seperate
files.

Refactoring:

- the _process_response pattern of throwing it in a zipstring
  is very common and can be a utility

- currently process_response is like two steps really - crack
  open SOAP request and then process response...

- and handle failures.

- replace % formatting statements in soapenvelopes with format {}

API deploy
        # Disable purge on delete entirely for non sandbox or DE orgs as it is
        # not allowed
        # FIXME: the task needs to be able to provide the org_type
        # org_type = self.task.org_config.org_type
        # if org_type.find('Sandbox') == -1 and org_type != 'Developer Edition'
        #    self.purge_on_delete = 'false'

list metadata:
            # Parse dates
            # FIXME: This was breaking things
            # for key in parse_dates:
            #    if result_data[key]:
            #        result_data[key] = dateutil.parser.parse(result_data[key])


"""
from cumulusci.salesforce_api.metadata.base import BaseMetadataApiCall
from cumulusci.salesforce_api.metadata.deploy import ApiDeploy
from cumulusci.salesforce_api.metadata.list_metadata import ApiListMetadata
from cumulusci.salesforce_api.metadata.retrieve_installed_packages import (
    ApiRetrieveInstalledPackages
)
from cumulusci.salesforce_api.metadata.retrieve_packaged import (
    ApiRetrievePackaged
)
from cumulusci.salesforce_api.metadata.retrieve_unpackaged import (
    ApiRetrieveUnpackaged
)

__all__ = [
    'BaseMetadataApiCall',
    'ApiDeploy',
    'ApiListMetadata',
    'ApiRetrieveInstalledPackages',
    'ApiRetrievePackaged',
    'ApiRetrieveUnpackaged']
