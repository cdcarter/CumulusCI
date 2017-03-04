""" Tests of the package zip builder """

import unittest
import collections

from base64 import b64decode
from zipfile import ZipFile
from StringIO import StringIO

from cumulusci.salesforce_api.package_zip import BasePackageZipBuilder
from cumulusci.salesforce_api.package_zip import CreatePackageZipBuilder
from cumulusci.salesforce_api.package_zip import DestructiveChangesZipBuilder
from cumulusci.salesforce_api.package_zip import InstallPackageZipBuilder


class UnimpressiveZipBuilder(BasePackageZipBuilder):
    """ A very basic ZipBuilder implementation for testing """
    def _populate_zip(self):
        self._write_file('README.md', '# Basic App')


class TestBaseZipBuilder(unittest.TestCase):
    """ Tests of the simple zip builder

    Functions.
    Is callable interface
    Base class raises notimplemented.
    Result is b64 encoded
    Write package.xml adds a package.xml
    """
    def test_zipbuilder(self):
        """ A naive builder creates a zip file as expected. """
        zipbuilder = UnimpressiveZipBuilder()

        zipstr = zipbuilder()
        zipstringio = StringIO(b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        self.assertIn('README.md', zipfile.namelist())
        self.assertIn('Basic App', zipfile.read('README.md'))

    def test_is_callable(self):
        """ A zipbuilder provides a callable api. """

        zipbuilder = UnimpressiveZipBuilder()
        self.assertIsInstance(zipbuilder, collections.Callable)

    def test_base_class_abstract(self):
        """ Base zipbuilder isn't implemented. """
        zipbuilder = BasePackageZipBuilder()
        with self.assertRaises(NotImplementedError):
            zipbuilder()

    def test_write_package_xml(self):
        """ Subclass API makes it east to add package.xml """
        zipbuilder = UnimpressiveZipBuilder()
        zipbuilder._open_zip()
        zipbuilder._write_package_xml('Test test test')

        zipstr = zipbuilder._encode_zip()
        zipstringio = StringIO(b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        self.assertIn('Test test test', zipfile.read('package.xml'))

    def test_create_package(self):
        """ The CreatePackageZipBuilder makes an empty package.xml with name """
        zipbuilder = CreatePackageZipBuilder('RoboAttack', '39.0')
        zipstr = zipbuilder()

        zipstringio = StringIO(b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        self.assertIn('RoboAttack', zipfile.read('package.xml'))
        self.assertNotIn('<members>', zipfile.read('package.xml'))

    def test_install_package(self):
        """ Install a package """
        zipbuilder = InstallPackageZipBuilder('npsp', '3.90')
        zipstr = zipbuilder()

        zipstringio = StringIO(b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        self.assertEqual(len(zipfile.namelist()), 2)
        self.assertIn(
            'installedPackages/npsp.installedPackage',
            zipfile.namelist()
        )

    def test_destructive_changes(self):
        """ The DestructiveChangesZipBuilder creates a zip with a
        destructiveChanges.xml """
        zipbuilder = DestructiveChangesZipBuilder('delete these')
        zipstr = zipbuilder()

        zipstringio = StringIO(b64decode(zipstr))
        zipfile = ZipFile(zipstringio, 'r')

        self.assertIn('package.xml', zipfile.namelist())
        self.assertIn('destructiveChanges.xml', zipfile.namelist())
        self.assertIn('delete these', zipfile.read('destructiveChanges.xml'))
        self.assertNotIn('<members>', zipfile.read('package.xml'))

