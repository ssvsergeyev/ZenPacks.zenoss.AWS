##############################################################################
#
# Copyright (coffee) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.AWS')

from zope.component import adapts
from zope.interface import implements

from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.Zuul.interfaces import IRRDDataSourceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSource


class AWSDataSource(PythonDataSource):
    '''
    Datasource used to capture datapoints.
    '''

    ZENPACKID = 'ZenPacks.zenoss.AWS'

    sourcetypes = ('AWSDataSource',)
    sourcetype = sourcetypes[0]

    # RRDDataSource
    component = '${here/id}'
    cycletime = 300

    # PythonDataSource
    plugin_classname = None

    # AmazonCloudWatchDataSource
    region = '${here/getRegionId}'

    _properties = PythonDataSource._properties + (
        {'id': 'region', 'type': 'string'},
    )


class IAWSDataSourceInfo(IRRDDataSourceInfo):
    '''
    API Info interface for AWSDataSource.
    '''

    region = schema.TextLine(
        group=_t('AWSDataSource'),
        title=_t('Region')
    )
    plugin_classname = schema.TextLine(
        group=_t('AWSDataSource'),
        title=_t('Plugin classname')
    )

    cycletime = schema.TextLine(
        group=_t('AWSDataSource'),
        title=_t('Cycletime')
    )


class AWSDataSourceInfo(RRDDataSourceInfo):
    '''
    API Info adapter factory for AWSDataSource.
    '''

    implements(IAWSDataSourceInfo)
    adapts(AWSDataSource)

    testable = False

    cycletime = ProxyProperty('cycletime')
    region = ProxyProperty('region')
    plugin_classname = ProxyProperty('plugin_classname')
