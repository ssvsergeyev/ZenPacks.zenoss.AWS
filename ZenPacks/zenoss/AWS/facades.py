###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013 Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################


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
        ec2m.setPerformanceMonitor('localhost')

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
