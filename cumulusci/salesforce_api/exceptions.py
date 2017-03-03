""" Exceptions for the Salesforce Metadata API """
from cumulusci.core.exceptions import CumulusCIException


class MetadataApiError(CumulusCIException):
    """ A generic exception with the MDAPI """
    def __init__(self, message, response):
        super(MetadataApiError, self).__init__(message)
        self.response = response


class MetadataComponentFailure(MetadataApiError):
    """ A failure due to a specific metadata component """
    pass

