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
from ZenPacks.zenoss.AWS.utils import updateToOne


class EC2Snapshot(AWSComponent):
    '''
    Model class for EC2Snapshot.
    '''

    meta_type = portal_type = 'EC2Snapshot'

    size = None
    status = None
    progress = None
    start_time = None
    description = None

    _properties = AWSComponent._properties + (
        {'id': 'size', 'type': 'int'},
        {'id': 'status', 'type': 'string'},
        {'id': 'progress', 'type': 'string'},
        {'id': 'start_time', 'type': 'string'},
        {'id': 'description', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('region', ToOne(ToManyCont, MODULE_NAME['EC2Region'], 'snapshots')),
        ('volume', ToOne(ToMany, MODULE_NAME['EC2Volume'], 'snapshots')),
        )

    def getRegionId(self):
        return self.region().id

    def getVolumeId(self):
        volume = self.volume()
        if volume:
            return volume.id

    def setVolumeId(self, id_):
        updateToOne(
            self.volume,
            self.region().volumes,
            CLASS_NAME['EC2Volume'],
            id_)


class IEC2SnapshotInfo(IComponentInfo):
    '''
    API Info interface for EC2Snapshot.
    '''

    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    volume = schema.Entity(title=_t(u'Volume'))
    size = schema.Int(title=_t(u'Volume Size in Bytes'))
    status = schema.TextLine(title=_t(u'Status'))
    progress = schema.TextLine(title=_t(u'Progress'))
    start_time = schema.TextLine(title=_t(u'Started'))
    description = schema.TextLine(title=_t(u'Description'))


class EC2SnapshotInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Snapshot.
    '''

    implements(IEC2SnapshotInfo)
    adapts(EC2Snapshot)

    size = ProxyProperty('size')
    status = ProxyProperty('status')
    progress = ProxyProperty('progress')
    start_time = ProxyProperty('start_time')
    description = ProxyProperty('description')

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
    def volume(self):
        return self._object.volume()
