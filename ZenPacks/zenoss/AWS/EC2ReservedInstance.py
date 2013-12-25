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

from zope.component import adapts
from zope.event import notify
from zope.interface import implements

from Products.AdvancedQuery import Eq

from Products.ZenRelations.RelSchema import ToMany, ToManyCont, ToOne

from Products.Zuul.catalog.events import IndexingEvent
from Products.Zuul.catalog.paths import DefaultPathReporter, relPath
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces import ICatalogTool
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import CLASS_NAME, MODULE_NAME, EC2INSTANCE_TYPES
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent
from ZenPacks.zenoss.AWS.utils import updateToOne, updateToMany


class EC2ReservedInstance(AWSComponent):
    meta_type = portal_type = 'EC2ReservedInstance'

    state = None
    instance_type = None

    _properties = AWSComponent._properties + (
        {'id': 'reserved_instance_id', 'type': 'string'},
        {'id': 'instance_type', 'type': 'string'},
        {'id': 'state', 'type': 'string'},
    )

    _relations = AWSComponent._relations + (
        ('region', ToOne(
            ToManyCont, MODULE_NAME['EC2Region'], 'reserved_instances')),

        ('zone', ToOne(
            ToMany, MODULE_NAME['EC2Zone'], 'reserved_instances')),
    )

    def monitored(self):
        ''' bool: Should be monitored?  '''
        return self.state and self.state.lower() == 'active'

    def getRegionId(self):
        return self.region().id

    def getZoneId(self):
        zone = self.zone()
        if zone:
            return zone.id

    def setZoneId(self, id_):
        updateToOne(
            self.zone,
            self.region().zones,
            CLASS_NAME['EC2Zone'],
            id_
        )


class IEC2ReservedInstanceInfo(IComponentInfo):
    reserved_instance_id = schema.TextLine(title=_t(u'Instance ID'))
    region = schema.Entity(title=_t(u'Region'))
    zone = schema.Entity(title=_t(u'Zone'))
    instance_type = schema.TextLine(title=_t(u'Instance Type'))
    state = schema.TextLine(title=_t(u'State'))


class EC2InstanceInfo(ComponentInfo):
    implements(IEC2ReservedInstanceInfo)
    adapts(EC2ReservedInstance)

    reserved_instance_id = ProxyProperty('reserved_instance_id')
    instance_type = ProxyProperty('instance_type')
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
    @info
    def zone(self):
        return self._object.zone()
