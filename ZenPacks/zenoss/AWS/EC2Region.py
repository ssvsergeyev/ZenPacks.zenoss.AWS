##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
LOG = logging.getLogger('zen.AWS')

import operator

from zope.component import adapts
from zope.interface import implements

from ZODB.transact import transact

from Products.ZenRelations.RelSchema import ToOne, ToManyCont

from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent


class EC2Region(AWSComponent):
    '''
    Model class for EC2Region.
    '''

    meta_type = portal_type = 'EC2Region'

    _instance_device_ids = None

    _properties = AWSComponent._properties

    _relations = AWSComponent._relations + (
        ('account', ToOne(ToManyCont, MODULE_NAME['EC2Account'], 'regions')),
        ('zones', ToManyCont(ToOne, MODULE_NAME['EC2Zone'], 'region')),
        ('instances', ToManyCont(ToOne, MODULE_NAME['EC2Instance'], 'region')),
        ('volumes', ToManyCont(ToOne, MODULE_NAME['EC2Volume'], 'region')),
        ('vpcs', ToManyCont(ToOne, MODULE_NAME['EC2VPC'], 'region')),
        ('vpc_subnets', ToManyCont(
            ToOne, MODULE_NAME['EC2VPCSubnet'], 'region')),
        ('elastic_ips', ToManyCont(
            ToOne, MODULE_NAME['EC2ElasticIP'], 'region')),
        ('reservations', ToManyCont(
            ToOne, MODULE_NAME['EC2Reservation'], 'region')),
        ('vpn_gateways', ToManyCont(
            ToOne, MODULE_NAME['VPNGateway'], 'region')),
    )

    def getDimension(self):
        return ''

    def getRegionId(self):
        return self.id

    @transact
    def discover_guests(self):
        '''
        Attempt to discover and link instance guest devices.
        '''
        map(operator.methodcaller('discover_guest'), self.instances())

        # First discovery. Initialize our instance device ids storage.
        if self._instance_device_ids is None:
            self._instance_device_ids = set(self.instances.objectIds())
            return

        instance_device_ids = set(self.instances.objectIds())
        terminated_device_ids = self._instance_device_ids.difference(
            instance_device_ids)

        # Delete guest devices for terminated instances.
        for device_id in terminated_device_ids:
            guest_device = self.findDeviceByIdExact(device_id)
            if guest_device:
                LOG.info(
                    'Deleting device %s after instance %s was terminated',
                    guest_device.titleOrId(),
                    guest_device.id)

                guest_device.deleteDevice()

        # Store instance device ids for next run.
        self._instance_device_ids = instance_device_ids


class IEC2RegionInfo(IComponentInfo):
    '''
    API Info interface for EC2Region.
    '''

    account = schema.Entity(title=_t(u'Account'))
    zone_count = schema.Int(title=_t(u'Number of Zones'))
    instance_count = schema.Int(title=_t(u'Number of Instances'))
    volume_count = schema.Int(title=_t(u'Number of Volumes'))
    vpc_count = schema.Int(title=_t(u'Number of VPCs'))
    vpc_subnet_count = schema.Int(title=_t(u'Number of VPC Subnets'))


class EC2RegionInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Region.
    '''

    implements(IEC2RegionInfo)
    adapts(EC2Region)

    @property
    @info
    def account(self):
        return self._object.device()

    @property
    def zone_count(self):
        return self._object.zones.countObjects()

    @property
    def instance_count(self):
        return self._object.instances.countObjects()

    @property
    def volume_count(self):
        return self._object.volumes.countObjects()

    @property
    def vpc_count(self):
        return self._object.vpcs.countObjects()

    @property
    def vpc_subnet_count(self):
        return self._object.vpc_subnets.countObjects()
