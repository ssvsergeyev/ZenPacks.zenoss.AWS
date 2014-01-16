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

from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import CLASS_NAME, MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent
from ZenPacks.zenoss.AWS.utils import updateToMany, updateToOne


class EC2ElasticIP(AWSComponent):
    '''
    Model class for EC2ElasticIP.
    '''

    meta_type = portal_type = 'EC2ElasticIP'

    public_ip = None
    private_ip_address = None
    instance_id = None
    domain = None
    network_interface_id = None
    network_interface_owner_id = None

    _properties = AWSComponent._properties + (
        {'id': 'public_ip', 'type': 'string'},
        {'id': 'private_ip_address', 'type': 'string'},
        {'id': 'instance_id', 'type': 'boolean'},
        {'id': 'domain', 'type': 'string'},
        {'id': 'network_interface_id', 'type': 'string'},
        {'id': 'network_interface_owner_id', 'type': 'string'},
    )

    _relations = AWSComponent._relations + (
        ('region', ToOne(
            ToManyCont, MODULE_NAME['EC2Region'], 'elastic_ips')),
    )


class IEC2ElasticIPInfo(IComponentInfo):
    '''
    API Info interface for EC2ElasticIP.
    '''

    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    public_ip = schema.TextLine(title=_t(u'Public IP'))
    private_ip_address = schema.TextLine(title=_t(u'Private IP address'))
    instance_id = schema.TextLine(title=_t(u'Instance ID'))
    domain = schema.TextLine(title=_t(u'Domain'))
    network_interface_id = schema.TextLine(title=_t(u'Network interface ID'))
    network_interface_owner_id = schema.TextLine(
        title=_t(u'Network interface owner ID')
    )


class EC2ElasticIPInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2ElasticIP.
    '''

    implements(IEC2ElasticIPInfo)
    adapts(EC2ElasticIP)

    public_ip = ProxyProperty('public_ip')
    private_ip_address = ProxyProperty('private_ip_address')
    instance_id = ProxyProperty('instance_id')
    domain = ProxyProperty('domain')
    network_interface_id = ProxyProperty('network_interface_id')
    network_interface_owner_id = ProxyProperty('network_interface_owner_id')

    @property
    @info
    def account(self):
        return self._object.device()

    @property
    @info
    def region(self):
        return self._object.region()
