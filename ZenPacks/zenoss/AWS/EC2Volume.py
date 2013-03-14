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


class EC2Volume(AWSComponent):
    '''
    Model class for EC2Volume.
    '''

    meta_type = portal_type = 'EC2Volume'

    create_time = None
    size = None
    iops = None
    status = None
    attach_data_status = None
    attach_data_devicepath = None

    _properties = AWSComponent._properties + (
        {'id': 'create_time', 'type': 'string'},
        {'id': 'size', 'type': 'int'},
        {'id': 'iops', 'type': 'int'},
        {'id': 'status', 'type': 'string'},
        {'id': 'attach_data_status', 'type': 'string'},
        {'id': 'attach_data_device', 'type': 'string'},
        {'id': 'devicepath', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('region', ToOne(ToManyCont, MODULE_NAME['EC2Region'], 'volumes')),
        ('zone', ToOne(ToMany, MODULE_NAME['EC2Zone'], 'volumes')),
        ('instance', ToOne(ToMany, MODULE_NAME['EC2Instance'], 'volumes')),
        )

    def getRRDTemplates(self):
        template_names = ['EC2Volume']

        if self.iops:
            template_names.append('EC2Volume-IOPS')

        templates = []
        for template_name in template_names:
            template = self.getRRDTemplateByName(template_name)
            if template:
                templates.append(template)

        return templates

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

    def getInstanceId(self):
        instance = self.instance()
        if instance:
            return instance.id

    def setInstanceId(self, id_):
        updateToOne(
            self.instance,
            self.region().instances,
            CLASS_NAME['EC2Instance'],
            id_)


class IEC2VolumeInfo(IComponentInfo):
    '''
    API Info interface for EC2Volume.
    '''

    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    zone = schema.Entity(title=_t(u'Zone'))
    instance = schema.Entity(title=_t(u'Instance'))
    create_time = schema.TextLine(title=_t(u'Created Time'))
    size = schema.Int(title=_t(u'Size in Bytes'))
    iops = schema.Int(title=_t(u'Provisioned IOPS'))
    status = schema.TextLine(title=_t(u'Status'))
    attach_data_status = schema.TextLine(title=_t(u'Attach Data Status'))
    attach_data_devicepath = schema.TextLine(title=_t(u'Attach Data Device'))


class EC2VolumeInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Volume.
    '''

    implements(IEC2VolumeInfo)
    adapts(EC2Volume)

    status = ProxyProperty('status')
    create_time = ProxyProperty('create_time')
    size = ProxyProperty('size')
    iops = ProxyProperty('iops')
    attach_data_status = ProxyProperty('attach_data_status')
    attach_data_devicepath = ProxyProperty('attach_data_devicepath')

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
    def instance(self):
        return self._object.instance()


class EC2VolumePathReporter(DefaultPathReporter):
    '''
    Path reporter for EC2Volume.
    '''

    def getPaths(self):
        paths = super(EC2VolumePathReporter, self).getPaths()

        zone = self.context.zone()
        if zone:
            paths.extend(relPath(zone, 'region'))

        instance = self.context.instance()
        if instance:
            paths.extend(relPath(instance, 'region'))

        return paths
