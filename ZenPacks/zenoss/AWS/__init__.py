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
        dc.setZenProperty('zPingMonitorIgnore',
                            True)

        dc.setZenProperty('zPythonClass', 'ZenPacks.zenoss.AWS.EC2Manager')
