##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenModel.DeviceComponent import DeviceComponent
from Products.ZenRelations.RelSchema import ToOne, ToManyCont


class EC2InstanceType(DeviceComponent, ManagedEntity):

    meta_type = portal_type = "EC2InstanceType"

    _properties = ManagedEntity._properties + (
        {'id': 'instLink', 'type': 'string', 'mode': 'w'},
        )

    _relations = ManagedEntity._relations + (
        ('manager', ToOne(ToManyCont,
            "ZenPacks.zenoss.AWS.EC2Manager", "instanceTypes")),
        )

    