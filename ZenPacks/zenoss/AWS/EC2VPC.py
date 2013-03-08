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


class EC2VPC(AWSComponent):
    '''
    Model class for EC2VPC.
    '''

    meta_type = portal_type = 'EC2VPC'

    cidr_block = None
    state = None
    collector = None

    _properties = AWSComponent._properties + (
        {'id': 'cidr_block', 'type': 'string'},
        {'id': 'state', 'type': 'string'},
        {'id': 'collector', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('region', ToOne(ToManyCont, MODULE_NAME['EC2Region'], 'vpcs')),
        ('vpc_subnets', ToMany(ToOne, MODULE_NAME['EC2VPCSubnet'], 'vpc')),
        )

    def getVPCSubnetIds(self):
        return sorted(self.vpc_subnets.objectIds())

    def setVPCSubnetIds(self, ids):
        updateToMany(
            relationship=self.vpc_subnets,
            root=self.region().vpc_subnets,
            type_=CLASS_NAME['EC2VPCSubnets'],
            ids=ids)


class IEC2VPCInfo(IComponentInfo):
    '''
    API Info interface for EC2VPC.
    '''

    state = schema.TextLine(title=_t(u'State'))
    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    cidr_block = schema.TextLine(title=_t(u'CIDR Block'))
    collector = schema.TextLine(title=_t(u'Collector'))
    vpc_subnet_count = schema.Int(title=_t('Number of VPC Subnets'))


class EC2VPCInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2VPC.
    '''

    implements(IEC2VPCInfo)
    adapts(EC2VPC)

    state = ProxyProperty('state')
    cidr_block = ProxyProperty('cidr_block')
    collector = ProxyProperty('collector')

    @property
    @info
    def account(self):
        return self._object.device()

    @property
    @info
    def region(self):
        return self._object.region()

    @property
    def vpc_subnet_count(self):
        return self._object.vpc_subnets.countObjects()
