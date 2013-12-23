##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.AWS')

import datetime
import time
import calendar
import random

from cStringIO import StringIO
from lxml import etree

from twisted.web.client import getPage

from twisted.internet import reactor, defer
from twisted.internet.defer import inlineCallbacks

from zope.component import adapts
from zope.interface import implements

from Products.ZenEvents import ZenEventClasses
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.Zuul.interfaces import IRRDDataSourceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSource, PythonDataSourcePlugin

from ZenPacks.zenoss.AWS.utils \
    import awsUrlSign, iso8601, result_errmsg, lookup_cwregion
from ZenPacks.zenoss.AWS.utils import addLocalLibPath

addLocalLibPath()
import boto.sqs



MAX_RETRIES = 3


class SQSDataSource(PythonDataSource):
    ZENPACKID = 'ZenPacks.zenoss.AWS'

    sourcetypes = ('Amazon SQS',)
    sourcetype = sourcetypes[0]

    # RRDDataSource
    component = '${here/id}'
    cycletime = 300

    # PythonDataSource
    plugin_classname = 'ZenPacks.zenoss.AWS.datasources.SQSDataSource.SQSDataSourcePlugin'

    # SQSDataSource
    region = '${here/getRegionId}'

    _properties = PythonDataSource._properties + (
        {'id': 'region', 'type': 'string'},
    )


class ISQSDataSourceInfo(IRRDDataSourceInfo):
    region = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Region'))


class SQSDataSourceInfo(RRDDataSourceInfo):
    implements(ISQSDataSourceInfo)
    adapts(SQSDataSource)
    region = ProxyProperty('region')


class SQSDataSourcePlugin(PythonDataSourcePlugin):
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
        )

    @classmethod
    def params(cls, datasource, context):
        return {
            'region': datasource.talesEval(datasource.region, context),
        }

    @inlineCallbacks
    def collect(self, config):
        if False: yield
        defer.returnValue(True)

    def onSuccess(self, results, config):
        data = {'events': [], 'values': {}, 'maps': []}
        for ds in config.datasources:
            region = ds.params['region']
            sqsconnection = boto.sqs.connect_to_region(region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )
            for queue in sqsconnection.get_all_queues():
                for message in queue.get_messages():
                    data['events'].append({
                        'summary': message._body,
                        'device': config.id,
                        'component': queue.name,
                        'eventKey': message.id,
                        'severity': ZenEventClasses.Info,
                        'eventClass': '/SQS/Message',
                    })

        data['events'].append({
            'device': config.id,
            'summary': 'successful collection',
            'eventKey': 'SQSDataSource_result',
            'severity': ZenEventClasses.Clear,
        })

        return data

    def onError(self, result, config):
        log.error('%s: %s', config.id, result)

        return {
            'events': [{
                'summary': 'error: %s' % result,
                'eventKey': 'SQSDataSource_result',
                'severity': ZenEventClasses.Error,
            }],
            'values': {},
            'maps': []
        }
