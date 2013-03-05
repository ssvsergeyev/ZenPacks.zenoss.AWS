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

from Globals import InitializeClass

from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenModel.DeviceComponent import DeviceComponent
from Products.ZenRelations.RelSchema import ToOne, ToManyCont


class EC2Zone(DeviceComponent, ManagedEntity):

    meta_type = portal_type = "EC2Zone"

    region = ''
    state = ''

    _properties = ManagedEntity._properties + (
        {'id': 'region',    'type': 'string', 'mode': 'w'},
        {'id': 'state',         'type': 'string', 'mode': 'w'},
        )

    _relations = ManagedEntity._relations + (
        ('manager', ToOne(ToManyCont,
            "ZenPacks.zenoss.AWS.EC2Manager", "zones")),
        )

    def device(self):
        return self.manager()

    def getRRDTemplateName(self):
        return 'EC2Zone'


InitializeClass(EC2Zone)
