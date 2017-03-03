class ApiUninstallVersion(ApiDeploy):

    def __init__(self, task, version, purge_on_delete=True):
        self.version = version
        if not version.number:
            self.package_zip = None
        else:
            self.package_zip = PackageZipBuilder(
                self.version.package.namespace).uninstall_package()
        super(ApiUninstallVersion, self).__init__(
            task, self.package_zip, purge_on_delete)
