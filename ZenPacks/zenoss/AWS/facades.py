
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from zope.interface import implements

from Products.Zuul.facades import ZuulFacade
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS.interfaces import IEC2ManagerFacade


class EC2ManagerFacade(ZuulFacade):
    implements(IEC2ManagerFacade)

    def add_ec2manager(self, accountname, accesskey, secretkey):
        """Handles adding a new EC2 Managers"""

        deviceRoot = self._dmd.getDmdRoot("Devices")
        device = deviceRoot.findDeviceByIdExact(accountname)
        if device:
            return False, _t("A device named %s already exists." % accountname)

        devicePath = "/Devices/AWS/EC2"

        dc = self._dmd.Devices.getOrganizer(devicePath)

        ec2m = dc.createInstance(accountname)

        ec2m.ec2accesskey = accesskey
        ec2m.ec2secretkey = secretkey

        return True

    def setEC2DeviceClass(self, id):
        """Handles updating the target device classes for linux and windows"""

        t = self.name()

        fileout = open('/tmp/test.txt', 'w')
        fileout.write(t)
        fileout.close()

        self.linuxDeviceClass = id

        return True
