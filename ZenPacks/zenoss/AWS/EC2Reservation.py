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


class EC2Reservation(AWSComponent):
    '''
    Model class for EC2Reservation.
    '''

    meta_type = portal_type = 'EC2Reservation'

    instance_type = None
    availability_zone = None
    duration = None
    description = None
    instance_tenancy = None
    offering_type = None
    state = None

    _properties = AWSComponent._properties + (
        {'id': 'instance_type', 'type': 'string'},
        {'id': 'availability_zone', 'type': 'string'},
        {'id': 'duration', 'type': 'boolean'},
        {'id': 'description', 'type': 'string'},
        {'id': 'instance_tenancy', 'type': 'string'},
        {'id': 'offering_type', 'type': 'string'},
        {'id': 'state', 'type': 'string'},
    )

    _relations = AWSComponent._relations + (
        ('account', ToOne(
            ToManyCont, MODULE_NAME['EC2Account'],
            'reservation')),
    )

    def getReservationId(self):
        return self.account().id


class IEC2ReservationInfo(IComponentInfo):
    '''
    API Info interface for EC2Reservation.
    '''

    account = schema.Entity(title=_t(u'Account'))
    instance_type = schema.TextLine(title=_t(u'Instance type'))
    availability_zone = schema.TextLine(title=_t(u'Availability zone'))
    duration = schema.TextLine(title=_t(u'Duration'))
    description = schema.TextLine(title=_t(u'Description'))
    instance_tenancy = schema.TextLine(title=_t(u'Instance tenancy'))
    offering_type = schema.TextLine(title=_t(u'Offering type'))
    state = schema.TextLine(title=_t(u'State'))


class EC2ReservationInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Reservation.
    '''

    implements(IEC2ReservationInfo)
    adapts(EC2Reservation)

    state = ProxyProperty('state')
    instance_type = ProxyProperty('instance_type')
    availability_zone = ProxyProperty('availability_zone')
    duration = ProxyProperty('duration')
    description = ProxyProperty('description')
    instance_tenancy = ProxyProperty('instance_tenancy')
    offering_type = ProxyProperty('offering_type')

    @property
    @info
    def account(self):
        return self._object.device()


class EC2ReservationPathReporter(DefaultPathReporter):
    '''
    Path reporter for EC2Reservation.
    '''

    def getPaths(self):
        return super(EC2ReservationPathReporter, self).getPaths()
