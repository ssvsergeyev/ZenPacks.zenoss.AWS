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


class EC2Image(AWSComponent):
    '''
    Model class for EC2Image.
    '''

    meta_type = portal_type = 'EC2Image'

    location = None
    state = None
    owner_id = None
    architecture = None
    platform = None
    image_type = None
    kernel_id = None
    ramdisk_id = None
    description = None
    block_device_mapping = None
    root_device_type = None
    root_device_name = None
    virtualization_type = None
    hypervisor = None
    instance_lifecycle = None

    _properties = AWSComponent._properties + (
        {'id': 'location', 'type': 'string'},
        {'id': 'state', 'type': 'string'},
        {'id': 'owner_id', 'type': 'boolean'},
        {'id': 'architecture', 'type': 'string'},
        {'id': 'platform', 'type': 'string'},
        {'id': 'image_type', 'type': 'string'},
        {'id': 'kernel_id', 'type': 'string'},
        {'id': 'ramdisk_id', 'type': 'string'},
        {'id': 'description', 'type': 'boolean'},
        {'id': 'block_device_mapping', 'type': 'string'},
        {'id': 'root_device_type', 'type': 'string'},
        {'id': 'root_device_name', 'type': 'string'},
        {'id': 'virtualization_type', 'type': 'string'},
        {'id': 'hypervisor', 'type': 'boolean'},
        {'id': 'instance_lifecycle', 'type': 'string'},
    )

    _relations = AWSComponent._relations + (
        ('account', ToOne(
            ToManyCont, MODULE_NAME['EC2Account'],
            'images')),
    )


class IEC2ImageInfo(IComponentInfo):
    '''
    API Info interface for EC2Image.
    '''

    account = schema.Entity(title=_t(u'Account'))
    location = schema.TextLine(title=_t(u'Location'))
    state = schema.TextLine(title=_t(u'State'))
    owner_id = schema.TextLine(title=_t(u'Owner ID'))
    architecture = schema.TextLine(title=_t(u'Architecture'))
    platform = schema.TextLine(title=_t(u'Platform'))
    image_type = schema.TextLine(title=_t(u'Image type'))
    kernel_id = schema.TextLine(title=_t(u'Kernel ID'))
    ramdisk_id = schema.TextLine(title=_t(u'Ramdisk ID'))
    description = schema.TextLine(title=_t(u'Description'))
    block_device_mapping = schema.TextLine(title=_t(u'Block device mapping'))
    root_device_type = schema.TextLine(title=_t(u'Root device type'))
    root_device_name = schema.TextLine(title=_t(u'Root device name'))
    virtualization_type = schema.TextLine(title=_t(u'Virtualization_type'))
    hypervisor = schema.TextLine(title=_t(u'Hypervisor'))
    instance_lifecycle = schema.TextLine(title=_t(u'Instance_lifecycle'))


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
    platform = ProxyProperty('platform')
    image_type = ProxyProperty('image_type')
    kernel_id = ProxyProperty('kernel_id')
    ramdisk_id = ProxyProperty('ramdisk_id')
    description = ProxyProperty('description')
    block_device_mapping = ProxyProperty('block_device_mapping')
    root_device_type = ProxyProperty('root_device_type')
    root_device_name = ProxyProperty('root_device_name')
    virtualization_type = ProxyProperty('virtualization_type')
    hypervisor = ProxyProperty('hypervisor')
    instance_lifecycle = ProxyProperty('instance_lifecycle')

    @property
    @info
    def account(self):
        return self._object.device()


class EC2ImagePathReporter(DefaultPathReporter):
    '''
    Path reporter for EC2Image.
    '''

    def getPaths(self):
        return super(EC2ImagePathReporter, self).getPaths()
