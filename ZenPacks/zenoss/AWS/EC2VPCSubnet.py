##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from zope.component import adapts
from zope.interface import implements

from Products.ZenRelations.RelSchema import ToOne, ToMany, ToManyCont

from Products.Zuul.catalog.paths import DefaultPathReporter, relPath
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import CLASS_NAME, MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent
from ZenPacks.zenoss.AWS.utils import updateToMany, updateToOne


class EC2VPCSubnet(AWSComponent):
    '''
    Model class for EC2VPCSubnet.
    '''

    meta_type = portal_type = 'EC2VPCSubnet'

    available_ip_address_count = None
    cidr_block = None
    defaultForAz = None
    mapPublicIpOnLaunch = None
    state = None

    _properties = AWSComponent._properties + (
        {'id': 'available_ip_address_count', 'type': 'int'},
        {'id': 'cidr_block', 'type': 'string'},
        {'id': 'defaultForAz', 'type': 'boolean'},
        {'id': 'mapPublicIpOnLaunch', 'type': 'boolean'},
        {'id': 'state', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('region', ToOne(ToManyCont, MODULE_NAME['EC2Region'], 'vpc_subnets')),
        ('vpc', ToOne(ToMany, MODULE_NAME['EC2VPC'], 'vpc_subnets')),
        ('zone', ToOne(ToMany, MODULE_NAME['EC2Zone'], 'vpc_subnets')),
        ('instances', ToMany(ToOne, MODULE_NAME['EC2Instance'], 'vpc_subnet')),
        )

    def getVPCId(self):
        vpc = self.vpc()
        if vpc:
            return vpc.id

    def setVPCId(self, id_):
        updateToOne(
            self.vpc,
            self.region().vpcs,
            CLASS_NAME['EC2VPC'],
            id_)

    def getZoneId(self):
        zone = self.zone()
        if zone:
            return zone.id

    def setZoneId(self, id_):
        updateToOne(
            self.zone,
            self.region().zones,
            CLASS_NAME['EC2Zone'],
            id_)

    def getInstanceIds(self):
        return sorted(self.instances.objectIds())

    def setInstanceIds(self, ids):
        updateToMany(
            relationship=self.instances,
            root=self.region().instances,
            type_=CLASS_NAME['EC2Instance'],
            ids=ids)


class IEC2VPCSubnetInfo(IComponentInfo):
    '''
    API Info interface for EC2VPCSubnet.
    '''

    state = schema.TextLine(title=_t(u'State'))
    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    zone = schema.Entity(title=_t(u'Zone'))
    vpc = schema.Entity(title=_t(u'VPC'))
    instance_count = schema.Int(title=_t(u'Number of Instances'))
    cidr_block = schema.TextLine(title=_t(u'CIDR Block'))
    available_ip_address_count = schema.Int(title=_t(u'Number of Available IP Addresses'))
    defaultForAz = schema.Bool(title=_t(u'Default for Zone'))
    mapPublicIpOnLaunch = schema.Bool(title=_t(u'Map Public IP on Launch'))


class EC2VPCSubnetInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2VPCSubnet.
    '''

    implements(IEC2VPCSubnetInfo)
    adapts(EC2VPCSubnet)

    state = ProxyProperty('state')
    cidr_block = ProxyProperty('cidr_block')
    available_ip_address_count = ProxyProperty('available_ip_address_count')
    defaultForAz = ProxyProperty('defaultForAz')
    mapPublicIpOnLaunch = ProxyProperty('mapPublicIpOnLaunch')

    @property
    @info
    def account(self):
        return self._object.device()

    @property
    @info
    def region(self):
        return self._object.region()

    @property
    @info
    def zone(self):
        return self._object.zone()

    @property
    @info
    def vpc(self):
        return self._object.vpc()

    @property
    def instance_count(self):
        return self._object.instances.countObjects()


class EC2VPCSubnetPathReporter(DefaultPathReporter):
    '''
    Path reporter for EC2VPCSubnet.
    '''

    def getPaths(self):
        paths = super(EC2VPCSubnetPathReporter, self).getPaths()

        zone = self.context.zone()
        if zone:
            paths.extend(relPath(zone, 'region'))

        return paths
