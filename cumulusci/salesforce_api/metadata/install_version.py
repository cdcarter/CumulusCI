
import base64
import StringIO

from cumulusci.utils import zip_subfolder
from cumulusci.salesforce_api.package_zip import InstallPackageZipBuilder
from cumulusci.salesforce_api.metadata.deploy import ApiDeploy
import requests


class ApiInstallVersion(ApiDeploy):

    def __init__(self, task, version, purge_on_delete=False):
        self.version = version
        # Construct and set the package_zip file
        if self.version.number:
            self.package_zip = InstallPackageZipBuilder(
                self.version.package.namespace,
                self.version.number).install_package()
        elif self.version.zip_url or self.version.repo_url:
            if self.version.repo_url:
                repo_url = self.version.repo_url
                git_ref = self.version.branch
                zip_url = '%s/archive/%s.zip' % (repo_url, git_ref)
            else:
                zip_url = self.version.zip_url
            # Deploy a zipped bundled downloaded from a URL
            try:
                zip_resp = requests.get(zip_url)
            except:
                raise ValueError('Failed to fetch zip from %s' %
                                 self.version.zip_url)
            zipfp = StringIO.StringIO(zip_resp.content)
            zipfile = ZipFile(zipfp, 'r')
            if not self.version.subfolder and not self.version.repo_url:
                zipfile.close()
                zipfp.seek(0)
                self.package_zip = base64.b64encode(zipfp.read())
            else:
                ignore_prefix = ''
                if self.version.repo_url:
                    # Get the top level folder from the zip
                    ignore_prefix = '%s/' % zipfile.namelist()[0].split('/')[0]
                # Extract a subdirectory from the zip
                subdirectory = ignore_prefix + self.version.subfolder
                subzip = zip_subfolder(
                    zipfile,
                    subdirectory,
                    self.version.namespace_token,
                    self.version.namespace)
                subzipfp = subzip.fp
                subzip.close()
                subzipfp.seek(0)
                self.package_zip = base64.b64encode(subzipfp.read())
        super(ApiInstallVersion, self).__init__(
            task, self.package_zip, purge_on_delete)
