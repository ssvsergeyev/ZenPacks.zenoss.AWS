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
        the setter even needs to be run. For this reason, this method
        must actually perform the discovery logic.
        '''
        self.discover_guests()

        return True

    def setDiscoverGuests(self, value):
        '''
        Attempt to discover and link instance guest devices.

        This method should typically never be called because the
        getDiscoverGuests method will always return the same value that
        the modeler plugin sets.
        '''
        self.discover_guests()

    def discover_guests(self):
        '''
        Attempt to discover and link instance guest devices.
        '''
        for region in self.regions():
            region.discover_guests()


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
