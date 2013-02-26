##############################################################################
#
# Copyright (C) Zenoss, Inc. 2012, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

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
