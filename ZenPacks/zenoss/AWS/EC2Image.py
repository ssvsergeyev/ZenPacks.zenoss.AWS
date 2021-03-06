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
from ZenPacks.zenoss.AWS.utils import updateToMany


class EC2Image(AWSComponent):
    '''
    Model class for EC2Image.
    '''

    meta_type = portal_type = 'EC2Image'

    location = None
    state = None
    owner_id = None
    architecture = None
    # platform = None
    image_type = None
    kernel_id = None
    ramdisk_id = None
    description = None
    block_device_mapping = None
    root_device_type = None
    root_device_name = None
    virtualization_type = None
    hypervisor = None

    _properties = AWSComponent._properties + (
        {'id': 'location', 'type': 'string'},
        {'id': 'state', 'type': 'string'},
        {'id': 'owner_id', 'type': 'boolean'},
        {'id': 'architecture', 'type': 'string'},
        # {'id': 'platform', 'type': 'string'},
        {'id': 'image_type', 'type': 'string'},
        {'id': 'kernel_id', 'type': 'string'},
        {'id': 'ramdisk_id', 'type': 'string'},
        {'id': 'description', 'type': 'boolean'},
        {'id': 'block_device_mapping', 'type': 'string'},
        {'id': 'root_device_type', 'type': 'string'},
        {'id': 'root_device_name', 'type': 'string'},
        {'id': 'virtualization_type', 'type': 'string'},
        {'id': 'hypervisor', 'type': 'boolean'},
    )

    _relations = AWSComponent._relations + (
        ('region', ToOne(
            ToManyCont, MODULE_NAME['EC2Region'], 'images')),

        ('instances', ToMany(
            ToOne, MODULE_NAME['EC2Instance'], 'image')),
    )

    def getInstanceIds(self):
        return sorted(self.instances.objectIds())

    def setInstanceIds(self, ids):
        updateToMany(
            relationship=self.instances,
            root=self.region().instances,
            type_=CLASS_NAME['EC2Instance'],
            ids=ids)


class IEC2ImageInfo(IComponentInfo):
    '''
    API Info interface for EC2Image.
    '''

    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))
    location = schema.TextLine(title=_t(u'Location'))
    # state = schema.TextLine(title=_t(u'State'))
    owner_id = schema.TextLine(title=_t(u'Owner ID'))
    architecture = schema.TextLine(title=_t(u'Architecture'))
    # platform = schema.TextLine(title=_t(u'Platform'))
    image_type = schema.TextLine(title=_t(u'Image Type'))
    kernel_id = schema.TextLine(title=_t(u'Kernel ID'))
    ramdisk_id = schema.TextLine(title=_t(u'RAM Disk ID'))
    description = schema.TextLine(title=_t(u'Description'))
    block_device_mapping = schema.TextLine(title=_t(u'Block Device Mapping'))
    root_device_type = schema.TextLine(title=_t(u'Root Device Type'))
    root_device_name = schema.TextLine(title=_t(u'Root Device Name'))
    virtualization_type = schema.TextLine(title=_t(u'Virtualization Type'))
    hypervisor = schema.TextLine(title=_t(u'Hypervisor'))
    instance_count = schema.Int(title=_t(u'Number of Instances'))


class EC2ImageInfo(ComponentInfo):
    '''
    API Info adapter factory for EC2Image.
    '''

    implements(IEC2ImageInfo)
    adapts(EC2Image)

    location = ProxyProperty('location')
    state = ProxyProperty('state')
    owner_id = ProxyProperty('owner_id')
    architecture = ProxyProperty('architecture')
    # platform = ProxyProperty('platform')
    image_type = ProxyProperty('image_type')
    kernel_id = ProxyProperty('kernel_id')
    ramdisk_id = ProxyProperty('ramdisk_id')
    description = ProxyProperty('description')
    block_device_mapping = ProxyProperty('block_device_mapping')
    root_device_type = ProxyProperty('root_device_type')
    root_device_name = ProxyProperty('root_device_name')
    virtualization_type = ProxyProperty('virtualization_type')
    hypervisor = ProxyProperty('hypervisor')

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
    @info
    def status(self):
        return self.state
