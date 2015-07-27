##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from Products.ZenModel.migrate.Migrate import Version
from Products.ZenModel.ZenPack import ZenPackMigration


def _removeObsoleteObjects(deviceCls):
    """Deletes the obsolete datasource objects.

    @param deviceCls {DeviceClass} The 'AWS' device class.
    """

    template = deviceCls.rrdTemplates.EC2Image
    if hasattr(template.datasources, "ImageState"):
        template.manage_deleteRRDDataSources(("ImageState",))

    template = deviceCls.rrdTemplates.EC2Instance
    if hasattr(template.datasources, "InstanceState"):
        template.manage_deleteRRDDataSources(("InstanceState",))

    template = deviceCls.rrdTemplates.EC2Snapshot
    if hasattr(template.datasources, "SnapshotStatus"):
        template.manage_deleteRRDDataSources(("SnapshotStatus",))


class RemoveObsoleteDataSource(ZenPackMigration):
    version = Version(2, 4, 0)

    reIndex = True

    def migrate(self, pack):
        try:
            ec2 = pack.dmd.Devices.AWS.EC2
        except AttributeError:
            return

        # Remove obsolete data sources and graph points.
        _removeObsoleteObjects(ec2)


RemoveObsoleteDataSource()
