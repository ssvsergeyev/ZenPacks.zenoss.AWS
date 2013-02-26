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

from zope.interface import implements

from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.device import DeviceInfo
from Products.Zuul.infos.component import ComponentInfo

from ZenPacks.zenoss.AWS.interfaces import *


class EC2ManagerInfo(DeviceInfo):
    implements(IEC2ManagerInfo)

    ec2accesskey = ProxyProperty('ec2accesskey')
    ec2secretkey = ProxyProperty('ec2secretkey')
    linuxDeviceClass = ProxyProperty('linuxDeviceClass')
    windowsDeviceClass = ProxyProperty('windowsDeviceClass')


class EC2InstanceInfo(ComponentInfo):
    implements(IEC2InstanceInfo)

    instance_id = ProxyProperty('instance_id')
    region = ProxyProperty('region')
    instance_type = ProxyProperty('instance_type')
    image_id = ProxyProperty('image_id')
    state = ProxyProperty('state')
    platform = ProxyProperty('platform')
    private_ip_address = ProxyProperty('private_ip_address')
    public_ip_address = ProxyProperty('public_ip_address')
    public_dns_name = ProxyProperty('public_dns_name')
    launch_time = ProxyProperty('launch_time')
