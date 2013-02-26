##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from Globals import InitializeClass

from Products.ZenRelations.RelSchema import ToOne, ToManyCont
from Products.ZenModel.Device import Device as baseDevice
from Products.ZenModel.ZenossSecurity import ZEN_VIEW


class EC2Manager(baseDevice):
    meta_type = portal_type = "EC2Manager"

    ec2accesskey = ''
    ec2secretkey = ''
    linuxDeviceClass = ''
    windowsDeviceClass = ''

    _properties = baseDevice._properties + (
        {'id': 'ec2accesskey', 'type': 'string', 'mode': 'w'},
        {'id': 'linuxDeviceClass', 'type': 'string', 'mode': 'w'},
        {'id': 'windowsDeviceClass', 'type': 'string', 'mode': 'w'},
        )

    _relations = baseDevice._relations + (
        ('instances', ToManyCont(ToOne,
            "ZenPacks.zenoss.AWS.EC2Instance", "manager")),
        )

    factory_type_information = (
        {
            'immediate_view': 'devicedetail',
            'actions':
            (
                {'id': 'events',
                'name': 'Events',
                'action': 'viewEvents',
                'permissions': (ZEN_VIEW, )
                },
                {'id': 'perfServer',
                'name': 'Graphs',
                'action': 'viewDevicePerformance',
                'permissions': (ZEN_VIEW, )
                }
            )
         },
        )

    def __init__(self, id, buildRelations=True):
        super(EC2Manager, self).__init__(id, buildRelations)


InitializeClass(EC2Manager)
