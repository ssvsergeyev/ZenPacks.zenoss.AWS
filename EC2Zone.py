##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenModel.DeviceComponent import DeviceComponent
from Products.ZenRelations.RelSchema import ToOne, ToMany, ToManyCont
from Products.ZenModel.ZenossSecurity import ZEN_VIEW
from boto.ec2.zone import Zone

class EC2Zone(DeviceComponent, ManagedEntity):
    """
    A DMD Device that represents a group of VMware hosts 
    that can run virtual devices.
    """

    meta_type = "EC2Zone"
    
    zone_name = ""
    state = ""
    region_name = ""
    messages = []

    _properties = (
        {'id':'zone_name',        'type':'string', 'mode':'w'},
        {'id':'state',           'type':'string', 'mode':'w'},
        {'id':'region_name',           'type':'string', 'mode':'w'},
        {'id':'messages',    'type':'list', 'mode':'w'})

    _relations = (
        ('manager', ToOne(ToManyCont, 
            "ZenPacks.zenoss.ZenAWS.EC2Manager", "zones")),
    )
    
    def device(self):
        return self.manager()


