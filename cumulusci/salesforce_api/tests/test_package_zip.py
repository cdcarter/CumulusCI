""" Tests of the package zip builder """

import unittest
from base64 import b64decode
from zipfile import ZipFile
from StringIO import StringIO

from cumulusci.salesforce_api.package_zip import BasePackageZipBuilder


class UnimpressiveZipBuilder(BasePackageZipBuilder):
    """ A very basic ZipBuilder implementation for testing """
    def _populate_zip(self):
        self._write_file('README.md', '# Basic App')
        self._write_package_xml('NA')


class TestBaseZipBuilder(unittest.TestCase):
    """ Tests of the simple zip builder """
    def test_zipbuilder(self):
        """ An end to end test of the naieve zipbuilder """
        zipbuilder = UnimpressiveZipBuilder()

        zipstr = zipbuilder()
        zipstringio = StringIO(b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        self.assertIn('README.md', zipfile.namelist())
        self.assertIn('package.xml', zipfile.namelist())

        self.assertIn('Basic App', zipfile.read('README.md'))
