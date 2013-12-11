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

from Products.Zuul.catalog.paths import DefaultPathReporter
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.AWS import MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent


class S3Bucket(AWSComponent):
    '''
    Model class for S3Bucket.
    '''

    meta_type = portal_type = 'S3Bucket'

    creation_date = None

    _properties = AWSComponent._properties + (
        {'id': 'creation_date', 'type': 'string'},
        )

    _relations = AWSComponent._relations + (
        ('account', ToOne(
            ToManyCont, MODULE_NAME['EC2Account'], 's3buckets')),
        )


class IS3BucketInfo(IComponentInfo):
    '''
    API Info interface for S3Bucket.
    '''

    creation_date = schema.TextLine(title=_t(u'Creation date'))
    account = schema.Entity(title=_t(u'Account'))


class S3BucketInfo(ComponentInfo):
    '''
    API Info adapter factory for S3Bucket.
    '''

    implements(IS3BucketInfo)
    adapts(S3Bucket)

    creation_date = ProxyProperty('creation_date')

    @property
    @info
    def account(self):
        return self._object.device()


class S3BucketPathReporter(DefaultPathReporter):
    '''
    Path reporter for S3Bucket.
    '''

    def getPaths(self):
        return super(S3BucketPathReporter, self).getPaths()
