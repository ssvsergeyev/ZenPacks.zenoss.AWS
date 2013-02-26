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

    #def name(self):
    #    return self.titleOrID()
