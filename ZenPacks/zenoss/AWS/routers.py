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

from Products.ZenUtils.Ext import DirectRouter, DirectResponse
from Products import Zuul


class EC2ManagerRouter(DirectRouter):
    def _getFacade(self):
        return Zuul.getFacade('ec2manager', self.context)

    def add_ec2manager(self, accountname, accesskey, secretkey):
        facade = self._getFacade()
        success = facade.add_ec2manager(
                accountname, accesskey, secretkey)

        if success:
            return DirectResponse.succeed()
        else:
            return DirectResponse.fail("FAILED to create")

    def set_ec2deviceclass(self, id):
        facade = self._getFacade()

        success = facade.setEC2DeviceClass(id)

        if success:
            return DirectResponse.succeed()
        else:
            return DirectResponse.fail("Something happened")
