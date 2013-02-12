##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from zope.interface import implements
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.decorators import info 

from ZenPacks.zenoss.ZenAWS.interfaces import ICWMonitorDataSourceInfo, \
                                              IEC2InstanceInfo, \
                                              IEC2InstanceTypeInfo, \
                                                IEC2ZoneInfo


class CWMonitorDataSourceInfo(RRDDataSourceInfo):
    implements(ICWMonitorDataSourceInfo)
    timeout = ProxyProperty('timeout')
    cycletime = ProxyProperty('cycletime')

    @property
    def testable(self):
        """
        We can NOT test this datsource against a specific device
        """
        return False


class EC2InstanceTypeInfo(ComponentInfo):
    implements(IEC2InstanceTypeInfo)

    @property
    @info
    def name(self):
        return self._object.name()


class EC2ZoneInfo(ComponentInfo):
    implements(IEC2ZoneInfo)

    @property
    @info
    def zone_name(self):
        return self._object.zone_name()
    
    @property
    @info
    def state(self):
        return self._object.state()

    @property
    @info
    def region_name(self):
        return self._object.region_name()
    
    @property
    @info
    def messages(self):
        return self._object.messages()


class EC2InstanceInfo(ComponentInfo):
    implements(IEC2InstanceInfo)

    @property
    @info
    def instance_id(self):
        return self._object.titleOrId()

    @property
    @info
    def device(self):
        return {
            'uid': self._object.getDeviceLink(),
            'name': self._object.getDeviceName()
        }

    @property
    @info
    def dns_name(self):
        return self._object.dns_name

    @property
    @info
    def aws_name(self):
        return self._object.aws_name

    @property
    @info
    def placement(self):
        return self._object.placement

    @property
    @info
    def instance_type(self):
        return self._object.instance_type

    @property
    @info
    def image_id(self):
        return self._object.image_id

    @property
    @info
    def state(self):
        return self._object.state

    @property
    @info
    def private_ip_addresses(self):
        pv_ip = self._object.private_ip_addresses
        if not pv_ip:
            pv_ip = []
        return pv_ip
