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

from Products.ZenRelations.RelSchema import ToMany, ToManyCont, ToOne

from Products.Zuul.catalog.paths import DefaultPathReporter, relPath
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import CLASS_NAME, MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent
from ZenPacks.zenoss.AWS.utils import updateToOne, updateToMany


class EC2Instance(AWSComponent):
    '''
    Model class for EC2Instance.
    '''

    meta_type = portal_type = 'EC2Instance'

    instance_id = None
    region = None
    instance_type = None
    image_id = None
    state = None
    platform = None
    private_ip_address = None
    public_dns_name = None
    launch_time = None

    _properties = AWSComponent._properties + (
        {'id': 'instance_id', 'type': 'string'},
        {'id': 'public_dns_name', 'type': 'string'},
        {'id': 'private_ip_address', 'type': 'string'},
        {'id': 'image_id', 'type': 'string'},
        {'id': 'instance_type', 'type': 'string'},
        {'id': 'launch_time', 'type': 'string'},
        {'id': 'state', 'type': 'string'},
        {'id': 'region', 'type': 'string'},
        {'id': 'platform', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('region', ToOne(
            ToManyCont, MODULE_NAME['EC2Region'], 'instances')),

        ('zone', ToOne(
            ToMany, MODULE_NAME['EC2Zone'], 'instances')),

        ('volumes', ToMany(
            ToOne, MODULE_NAME['EC2Volume'], 'instance')),

        ('vpc_subnet', ToOne(
            ToMany, MODULE_NAME['EC2VPCSubnet'], 'instances')),
        )

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

    def getVolumeIds(self):
        return sorted(self.volumes.objectIds())

    def setVolumeIds(self, ids):
        updateToMany(
            self.volumes,
            self.region().volumes,
            CLASS_NAME['EC2Volume'],
            ids)

    def getVPCSubnetId(self):
        vpc_subnet = self.vpc_subnet()
        if vpc_subnet:
            return vpc_subnet.id

    def setVPCSubnetId(self, id_):
        updateToOne(
            self.vpc_subnet,
            self.region().vpc_subnets,
            CLASS_NAME['EC2VPCSubnet'],
            id_)


class IEC2InstanceInfo(IComponentInfo):
    '''
    API Info interface for EC2Instance.
    '''

    state = schema.TextLine(title=_t(u'State'))
    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    zone = schema.Entity(title=_t(u'Zone'))
    vpc_subnet = schema.Entity(title=_t(u'VPC Subnet'))
    instance_id = schema.TextLine(title=_t(u'Instance ID'))
    instance_type = schema.TextLine(title=_t(u'Instance Type'))
    image_id = schema.TextLine(title=_t(u'Image ID'))
    platform = schema.TextLine(title=_t(u'Platform'))
    public_dns_name = schema.TextLine(title=_t(u'Public DNS Name'))
    private_ip_address = schema.TextLine(title=_t(u'Private IP Address'))
    launch_time = schema.TextLine(title=_t(u'Launch Time'))
    volume_count = schema.Int(title=_t(u'Number of Volumes'))


class EC2InstanceInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Instance.
    '''

    implements(IEC2InstanceInfo)
    adapts(EC2Instance)

    instance_id = ProxyProperty('instance_id')
    instance_type = ProxyProperty('instance_type')
    image_id = ProxyProperty('image_id')
    state = ProxyProperty('state')
    platform = ProxyProperty('platform')
    public_dns_name = ProxyProperty('public_dns_name')
    private_ip_address = ProxyProperty('private_ip_address')
    launch_time = ProxyProperty('launch_time')

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
    def vpc_subnet(self):
        return self._object.vpc_subnet()

    @property
    def volume_count(self):
        return self._object.volumes.countObjects()


class EC2InstancePathReporter(DefaultPathReporter):
    '''
    Path reporter for EC2Instance.
    '''

    def getPaths(self):
        paths = super(EC2InstancePathReporter, self).getPaths()

        zone = self.context.zone()
        if zone:
            paths.extend(relPath(zone, 'region'))

        vpc_subnet = self.context.vpc_subnet()
        if vpc_subnet:
            paths.extend(relPath(vpc_subnet, 'region'))

            vpc = vpc_subnet.vpc()
            if vpc:
                paths.extend(relPath(vpc, 'region'))

        return paths
