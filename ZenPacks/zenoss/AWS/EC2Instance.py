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
    detailed_monitoring = None

    # Used to restore user-defined production state when a stopped
    # instance is resumed.
    _running_prodstate = 1000

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
        {'id': 'detailed_monitoring', 'type': 'boolean'},
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

    def getIconPath(self):
        '''
        Return the path to an icon for this component.
        '''
        if self.detailed_monitoring:
            img_name = 'EC2Instance-cw'
        else:
            img_name = 'EC2Instance'

        return '/++resource++aws/img/%s.png' % img_name

    def monitored(self):
        '''
        Return True if this instance should be monitored. False
        otherwise.
        '''
        if self.state and self.state.lower() == 'running':
            return True

        return False

    def getRRDTemplates(self):
        template_names = []

        if self.detailed_monitoring:
            template_names.append('EC2Instance-Detailed')
        else:
            template_names.append('EC2Instance')

        template_names.append('EC2Instance-Custom')

        templates = []
        for template_name in template_names:
            template = self.getRRDTemplateByName(template_name)
            if template:
                templates.append(template)

        return templates

    def getDimension(self):
        return 'InstanceId=%s' % self.id

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

    def vpc(self):
        '''
        Return the VPC for this instance or None.
        '''
        subnet = self.vpc_subnet()
        if subnet:
            return subnet.vpc()

    def guest_manage_ip(self):
        '''
        Return the best manageIp for this instance's guest device or
        None if no good option is found.
        '''
        if self.vpc():
            return self.private_ip_address

        if self.public_dns_name:
            try:
                import socket
                return socket.gethostbyname(self.public_dns_name)
            except socket.gaierror:
                pass

    def guest_device(self):
        '''
        Return guest device object or None if not found.
        '''
        # OPTIMIZE: On systems with a large number of devices it might
        # be more optimal to first try searching only within
        # instance.guest_deviceclass()

        device = self.findDeviceByIdExact(self.id)
        if device:
            return device

        if self.title and self.title != self.id:
            device = self.findDeviceByIdExact(self.title)
            if device:
                return device

        ip_address = self.guest_manage_ip()
        if ip_address:
            device = self.findDeviceByIdOrIp(ip_address)
            if device:
                return device

    def guest_deviceclass(self):
        '''
        Return destination device class for this instance's guest device
        or None if not set.
        '''
        path = None
        if self.platform and 'windows' in self.platform.lower():
            path = self.device().windowsDeviceClass
        else:
            path = self.device().linuxDeviceClass

        if path:
            return self.getDmdRoot('Devices').createOrganizer(path)

    def guest_collector(self):
        '''
        Return the best collector for this instance's guest device.
        '''
        vpc = self.vpc()
        if vpc and vpc.collector:
            collector = self.getDmdRoot('Monitors').Performance._getOb(
                vpc.collector, None)

            if collector:
                return collector

        return self.getPerformanceServer()

    def create_guest(self):
        '''
        Create guest device for this instance if it doesn't already
        exist.
        '''
        deviceclass = self.guest_deviceclass()
        if not deviceclass:
            return

        manage_ip = self.guest_manage_ip()
        if not manage_ip:
            return

        collector = self.guest_collector()
        if not collector:
            return

        if self.guest_device():
            return

        LOG.info(
            'instance %s running. Discovering guest device',
            self.titleOrId())

        device = deviceclass.createInstance(self.id)
        device.title = self.title
        device.setManageIp(manage_ip)
        device.setPerformanceMonitor(collector.id)
        device.setProdState(self._running_prodstate)
        device.index_object()
        notify(IndexingEvent(device))

        # Schedule a modeling job for the new device.
        device.collectDevice(setlog=False, background=True)

    def discover_guest(self):
        '''
        Attempt to discover and link guest device.
        '''
        if not self.state:
            return

        deviceclass = self.guest_deviceclass()
        if not deviceclass:
            return

        if self.state.lower() == 'running':
            guest_device = self.guest_device()
            if guest_device:
                if guest_device.productionState != self._running_prodstate:
                    LOG.info(
                        'instance %s running. Changing guest device '
                        'to production',
                        self.titleOrId())

                    guest_device.setProdState(self._running_prodstate)
            else:
                self.create_guest()

        elif self.state.lower() == 'stopped':
            guest_device = self.guest_device()
            if guest_device:
                if guest_device.productionState != -1:
                    LOG.info(
                        'instance %s stopped. Decommissioning guest device',
                        self.titleOrId())

                    guest_device.setProdState(-1)


class IEC2InstanceInfo(IComponentInfo):
    '''
    API Info interface for EC2Instance.
    '''

    state = schema.TextLine(title=_t(u'State'))
    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    zone = schema.Entity(title=_t(u'Zone'))
    vpc = schema.Entity(title=_t(u'VPC'))
    vpc_subnet = schema.Entity(title=_t(u'VPC Subnet'))
    instance_id = schema.TextLine(title=_t(u'Instance ID'))
    instance_type = schema.TextLine(title=_t(u'Instance Type'))
    image_id = schema.TextLine(title=_t(u'Image ID'))
    platform = schema.TextLine(title=_t(u'Platform'))
    public_dns_name = schema.TextLine(title=_t(u'Public DNS Name'))
    private_ip_address = schema.TextLine(title=_t(u'Private IP Address'))
    launch_time = schema.TextLine(title=_t(u'Launch Time'))
    detailed_monitoring = schema.Bool(title=_t(u'Detailed Monitoring'))
    volume_count = schema.Int(title=_t(u'Number of Volumes'))
    guest_device = schema.Entity(title=_t(u'Guest Device'))


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
    detailed_monitoring = ProxyProperty('detailed_monitoring')

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
    @info
    def vpc_subnet(self):
        return self._object.vpc_subnet()

    @property
    def volume_count(self):
        return self._object.volumes.countObjects()

    @property
    @info
    def guest_device(self):
        return self._object.guest_device()


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


def ec2_instance_for_device(device):
    '''
    Return EC2 instance for device or None.
    '''
    try:
        ec2_deviceclass = device.getDmdRoot('Devices').getOrganizer('/AWS/EC2')
    except Exception:
        return

    results = ICatalogTool(ec2_deviceclass).search(
        types=(CLASS_NAME['EC2Instance'],),
        query=Eq('id', device.id))

    for brain in results:
        return brain.getObject()


class DeviceLinkProvider(object):
    '''
    Provides a link on the device overview page to the EC2 instance the
    device is running within.
    '''
    def __init__(self, device):
        self._device = device

    def getExpandedLinks(self):
        instance = ec2_instance_for_device(self._device)
        if instance:
            return ['<a href="%s">EC2 Instance</a>' % (
                instance.getPrimaryUrlPath())]

        return []
