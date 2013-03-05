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


class EC2Instance(DeviceComponent, ManagedEntity):

    meta_type = portal_type = "EC2Instance"

    instance_id = ''
    region = ''
    instance_type = ''
    image_id = ''
    state = ''
    platform = ''
    private_ip_address = ''
    public_ip_address = ''
    public_dns_name = ''
    launch_time = ''

    _properties = ManagedEntity._properties + (
        {'id': 'instance_id',        'type': 'string', 'mode': 'w'},
        {'id': 'public_dns_name',    'type': 'string', 'mode': 'w'},
        {'id': 'private_ip_address',         'type': 'string', 'mode': 'w'},
        {'id': 'image_id',           'type': 'string', 'mode': 'w'},
        {'id': 'instance_type',      'type': 'string', 'mode': 'w'},
        {'id': 'launch_time',        'type': 'string', 'mode': 'w'},
        {'id': 'state',              'type': 'string', 'mode': 'w'},
        {'id': 'region',             'type': 'string', 'mode': 'w'},
        {'id': 'platform',           'type': 'string', 'mode': 'w'},
        )

    _relations = ManagedEntity._relations + (
        ('manager', ToOne(ToManyCont,
            "ZenPacks.zenoss.AWS.EC2Manager", "instances")),
        )

    def device(self):
        return self.manager()

    def getRRDTemplateName(self):
        return 'EC2Instance'

InitializeClass(EC2Instance)
