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

from Products.ZenModel.Device import Device

from Products.ZenRelations.RelSchema import ToManyCont, ToOne

from Products.Zuul import getFacade
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.device import DeviceInfo
from Products.Zuul.interfaces.device import IDeviceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import MODULE_NAME


class EC2Account(Device):
    '''
    Model class for EC2Account.
    '''
    meta_type = portal_type = 'EC2Account'

    ec2accesskey = None
    ec2secretkey = None
    linuxDeviceClass = None
    windowsDeviceClass = None
    _setDiscoverGuests = None

    _properties = Device._properties + (
        {'id': 'ec2accesskey', 'type': 'string'},
        {'id': 'ec2secretkey', 'type': 'string'},
        {'id': 'linuxDeviceClass', 'type': 'string'},
        {'id': 'windowsDeviceClass', 'type': 'string'},
    )

    _relations = Device._relations + (
        ('regions', ToManyCont(
            ToOne, MODULE_NAME['EC2Region'], 'account')),
        ('s3buckets', ToManyCont(
            ToOne, MODULE_NAME['S3Bucket'], 'account')),
    )

    def getIconPath(self):
        ''' Return the path to an icon for this component.  '''
        return '/++resource++aws/img/%s.png' % self.meta_type

    def getDiscoverGuests(self):
        '''
        Attempt to discover and link instance guest devices.

        The modeler plugin calls setDiscoverGuests which will cause
        ApplyDataMap to call this getter method first to validate that
        the setter even needs to be run.
        This method will return what was set from a previous run.
        Regenerate the current_model, if it matches the previous model_run
        send the previous value.
        '''

        current_model = []
        for region in self.regions():
            for instance in region.instances():
                guest_device = instance.guest_device()
                if guest_device:
                   current_model.append((instance.id, guest_device.productionState))
        current_model = sorted(current_model)
        try:
            if current_model == self._setDiscoverGuests[1]:
                return self._setDiscoverGuests[0]
            else:
                return []
        except Exception:
            return []

    def setDiscoverGuests(self, value):
        '''
        Attempt to discover and link instance guest devices.
        Gather the current model and incoming value, save it for comparison later.
        '''
        self.discover_guests()
        current_model = []
        for region in self.regions():
            for instance in region.instances():
                guest_device = instance.guest_device()
                if guest_device:
                   current_model.append((instance.id, guest_device.productionState))
        current_model = sorted(current_model)
        self._setDiscoverGuests = (value, current_model)

    def discover_guests(self):
        '''
        Attempt to discover and link instance guest devices.
        '''
        for region in self.regions():
            region.discover_guests()

    def getClearEvents(self):
        self.clear_events()
        return True

    def setClearEvents(self, value):
        self.clear_events()

    def clear_events(self):
        zep = getFacade('zep')
        zep_filter = zep.createEventFilter(
            element_identifier=(self.id),
            event_class=('/Status'),
            severity=(5),
            status=(0, 1)
        )
        results = zep.getEventSummariesGenerator(filter=zep_filter)

        component_list = [x.getObject().id for x in self.componentSearch()]
        for res in results:
            key = res['occurrence'][0]['actor'].get('element_sub_identifier')
            if key and key not in component_list:
                del_filter = zep.createEventFilter(uuid=res['uuid'])
                zep.closeEventSummaries(eventFilter=del_filter)

    def getRegionId(self):
        return ""

    def getDimension(self):
        return ""


class IEC2AccountInfo(IDeviceInfo):
    '''
    API Info interface for EC2Account.
    '''

    ec2accesskey = schema.TextLine(title=_t(u'EC2 Access Key'))
    ec2secretkey = schema.TextLine(title=_t(u'EC2 Secret Key'))
    linuxDeviceClass = schema.Entity(title=_t(u'Linux Device Class'))
    windowsDeviceClass = schema.Entity(title=_t(u'Windows Device Class'))


class EC2AccountInfo(DeviceInfo):
    '''
    API Info adapter factory for EC2Account.
    '''

    implements(IEC2AccountInfo)
    adapts(EC2Account)

    ec2accesskey = ProxyProperty('ec2accesskey')
    ec2secretkey = ProxyProperty('ec2secretkey')

    @property
    @info
    def linuxDeviceClass(self):
        try:
            return self._object.getDmdRoot('Devices').getOrganizer(
                self._object.linuxDeviceClass)

        except Exception:
            return None

    @property
    @info
    def windowsDeviceClass(self):
        try:
            return self._object.getDmdRoot('Devices').getOrganizer(
                self._object.windowsDeviceClass)

        except Exception:
            return None
