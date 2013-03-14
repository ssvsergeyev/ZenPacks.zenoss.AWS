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

from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import CLASS_NAME, MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent
from ZenPacks.zenoss.AWS.utils import updateToMany


class EC2Zone(AWSComponent):
    '''
    Model class for EC2Zone.
    '''

    meta_type = portal_type = 'EC2Zone'

    state = None

    _properties = AWSComponent._properties + (
        {'id': 'state', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('region', ToOne(ToManyCont, MODULE_NAME['EC2Region'], 'zones')),
        ('instances', ToMany(ToOne, MODULE_NAME['EC2Instance'], 'zone')),
        ('volumes', ToMany(ToOne, MODULE_NAME['EC2Volume'], 'zone')),
        ('vpc_subnets', ToMany(ToOne, MODULE_NAME['EC2VPCSubnet'], 'zone')),
        )

    def getRegionId(self):
        return self.region().id

    def getInstanceIds(self):
        return sorted(self.instances.objectIds())

    def setInstanceIds(self, ids):
        updateToMany(
            relationship=self.instances,
            root=self.region().instances,
            type_=CLASS_NAME['EC2Instance'],
            ids=ids)

    def getVolumeIds(self):
        return sorted(self.volumes.objectIds())

    def setVolumeIds(self, ids):
        updateToMany(
            relationship=self.volumes,
            root=self.region().volumes,
            type_=CLASS_NAME['EC2Volumes'],
            ids=ids)

    def getVPCSubnetIds(self):
        return sorted(self.vpc_subnets.objectIds())

    def setVPCSubnetIds(self, ids):
        updateToMany(
            relationship=self.vpc_subnets,
            root=self.region().vpc_subnets,
            type_=CLASS_NAME['EC2VPCSubnets'],
            ids=ids)


class IEC2ZoneInfo(IComponentInfo):
    '''
    API Info interface for EC2Zone.
    '''

    state = schema.TextLine(title=_t(u'State'))
    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    instance_count = schema.Int(title=_t(u'Number of Instances'))
    volume_count = schema.Int(title=_t(u'Number of Volumes'))
    vpc_subnet_count = schema.Int(title=_t(u'Number of VPC Subnets'))


class EC2ZoneInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Zone.
    '''

    implements(IEC2ZoneInfo)
    adapts(EC2Zone)

    state = ProxyProperty('state')

    @property
    @info
    def account(self):
        return self._object.device()

    @property
    @info
    def region(self):
        return self._object.region()

    @property
    def instance_count(self):
        return self._object.instances.countObjects()

    @property
    def volume_count(self):
        return self._object.volumes.countObjects()

    @property
    def vpc_subnet_count(self):
        return self._object.vpc_subnets.countObjects()
