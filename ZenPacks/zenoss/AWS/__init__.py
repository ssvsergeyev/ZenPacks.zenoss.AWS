##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
LOG = logging.getLogger('zen.AWS')

from Products.ZenModel.ZenPack import ZenPackBase


class ZenPack(ZenPackBase):
    "ZenPack Loader that loads zProperties used by ZenAWS"

    def install(self, app):
        ZenPackBase.install(self, app)
        dc = app.dmd.Devices.createOrganizer('/AWS/EC2')

        dc.setZenProperty('zCollectorPlugins',
                            ('aws.EC2',))

        dc.setZenProperty('zPythonClass', 'ZenPacks.zenoss.AWS.EC2Manager')

