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

from Products.Zuul.form import schema
from Products.Zuul.interfaces.device import IDeviceInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.interfaces import IFacade

from Products.Zuul.utils import ZuulMessageFactory as _t


class IEC2ManagerFacade(IFacade):
    def add_ec2manager(self, accountname, accesskey, secretkey):
        """Add EC2 Manager."""


class IEC2ManagerInfo(IDeviceInfo):
    ec2accesskey = schema.TextLine(title=_t(u'EC2 Access Key'), readonly=True)
    ec2secretkey = schema.TextLine(title=_t(u'EC2 Secret Key'), readonly=True)
    linuxDeviceClass = schema.TextLine(title=_t(u'Linux Device Class'), readonly=True)
    windowsDeviceClass = schema.TextLine(title=_t(u'Windows Device Class'), readonly=True)


class IEC2InstanceInfo(IComponentInfo):
    instance_id = schema.TextLine(title=_t(u'Instance ID'), readonly=True)
    region = schema.TextLine(title=_t(u'Region'), readonly=True)
    instance_type = schema.TextLine(title=_t(u'Instance Type'), readonly=True)
    image_id = schema.TextLine(title=_t(u'Image ID'), readonly=True)
    state = schema.TextLine(title=_t(u'State'), readonly=True)
    platform = schema.TextLine(title=_t(u'Platform'), readonly=True)
    private_ip_address = schema.TextLine(title=_t(u'Private IP Address'), readonly=True)
    public_ip_address = schema.TextLine(title=_t(u'Public IP Address'), readonly=True)
    public_dns_name = schema.TextLine(title=_t(u'Public DNS Name'), readonly=True)
    launch_time = schema.TextLine(title=_t(u'Launch Time'), readonly=True)


class IEC2VPCInfo(IComponentInfo):
    region = schema.TextLine(title=_t(u'Region'), readonly=True)
    state = schema.TextLine(title=_t(u'State'), readonly=True)
    cidr_block = schema.TextLine(title=_t(u'CIDR Block'), readonly=True)
    collector = schema.TextLine(title=_t(u'Collector'), readonly=True)


class IEC2ZoneInfo(IComponentInfo):
    region = schema.TextLine(title=_t(u'Region'), readonly=True)
    state = schema.TextLine(title=_t(u'State'), readonly=True)


class IEC2VolumeInfo(IComponentInfo):
    region = schema.TextLine(title=_t(u'Region'), readonly=True)
    state = schema.TextLine(title=_t(u'State'), readonly=True)
    zone = schema.TextLine(title=_t(u'Zone'), readonly=True)
    size = schema.TextLine(title=_t(u'Size'), readonly=True)
    create_time = schema.TextLine(title=_t(u'Create Time'), readonly=True)
