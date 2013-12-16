##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
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

from ZenPacks.zenoss.AWS import CLASS_NAME, MODULE_NAME
from ZenPacks.zenoss.AWS.AWSComponent import AWSComponent
from ZenPacks.zenoss.AWS.utils import updateToMany


class SQSQueue(AWSComponent):
    meta_type = portal_type = 'SQSQueue'

    _relations = AWSComponent._relations + (
        ('region', ToOne(ToManyCont, MODULE_NAME['EC2Region'], 'queues')),
    )


class ISQSQueueInfo(IComponentInfo):
    account = schema.Entity(title=_t(u'Account'))
    region = schema.Entity(title=_t(u'Region'))


class SQSQueueInfo(ComponentInfo):
    implements(ISQSQueueInfo)
    adapts(SQSQueue)

    @property
    @info
    def account(self):
        return self._object.device()

    @property
    @info
    def region(self):
        return self._object.region()
