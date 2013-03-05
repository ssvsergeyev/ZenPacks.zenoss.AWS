###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013 Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

import logging
log = logging.getLogger('zen.AWS')

import datetime
import time
import calendar
import re

from twisted.web.client import getPage

from twisted.internet import reactor, defer
from twisted.internet.defer import inlineCallbacks


from zope.component import adapts
from zope.interface import implements

from Products.Zuul.form import schema
from Products.ZenUtils.Utils import prepId
from Products.Zuul.infos import ProxyProperty
from Products.ZenEvents import ZenEventClasses
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.Zuul.interfaces import IRRDDataSourceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSource, PythonDataSourcePlugin

from ZenPacks.zenoss.AWS.utils \
    import awsUrlSign, result_errmsg, lookup_cwregion


class AWSDataSource(PythonDataSource):
    """Datasource used to capture datapoints from AWS CloudWatch."""

    ZENPACKID = 'ZenPacks.zenoss.AWS'

    sourcetypes = ('AWS',)
    sourcetype = sourcetypes[0]

    plugin_classname = 'ZenPacks.zenoss.AWS.datasources.AWSDataSource.AWSDataSourcePlugin'

    region = ''
    namespace = ''
    result_component_key = ''

    _properties = PythonDataSource._properties + (
        {'id': 'region', 'type': 'string'},
        {'id': 'namespace', 'type': 'string'},
        {'id': 'result_component_key', 'type': 'string'},
        )


class IAWSDataSourceInfo(IRRDDataSourceInfo):

    namespace = schema.TextLine(
        group=_t('AWS'),
        title=_t('Namespace'))

    region = schema.TextLine(
        group=_t('AWS'),
        title=_t('Region'))

    result_component_key = schema.TextLine(
        group=_t('AWS'),
        title=_t('Result Component Key'))


class AWSDataSourceInfo(RRDDataSourceInfo):
    implements(IAWSDataSourceInfo)
    adapts(AWSDataSource)

    testable = False

    cycletime = ProxyProperty('cycletime')

    region = ProxyProperty('region')
    namespace = ProxyProperty('namespace')
    result_component_key = ProxyProperty('result_component_key')


class AWSDataSourcePlugin(PythonDataSourcePlugin):
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
        )

    @classmethod
    def config_key(cls, datasource, context):

        params = cls.params(datasource, context)
        return(
            context.device().id,
            datasource.getCycleTime(context),
            datasource.rrdTemplate().id,
            datasource.id,
            datasource.plugin_classname,
            )

    @classmethod
    def params(cls, datasource, context):
        params = {}

        params['result_component_key'] = datasource.talesEval(
            datasource.result_component_key, context)
        params['namespace'] = datasource.talesEval(
            datasource.namespace, context)
        params['region'] = datasource.talesEval(
            datasource.region, context)

        return params

    @inlineCallbacks
    def collect(self, config):

        results = []

        ds0 = config.datasources[0]

        accesskey = ds0.ec2accesskey
        secretkey = ds0.ec2secretkey

        cycletime = 300

        # Static for performance collection
        httpVerb = 'GET'
        uriRequest = '/'

        httpRequest = {}
        httpRequest['Action'] = 'GetMetricStatistics'
        httpRequest['StartTime'] = (datetime.datetime.utcnow() - \
            datetime.timedelta(seconds=cycletime)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        httpRequest['EndTime'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        httpRequest['Period'] = 300
        httpRequest['SignatureMethod'] = 'HmacSHA256'
        httpRequest['SignatureVersion'] = '2'
        httpRequest['Version'] = '2010-08-01'
        httpRequest['Statistics.member.1'] = 'Maximum'

        backoff = 0

        def sleep(secs):
            d = defer.Deferred()
            reactor.callLater(secs, d.callback, None)
            return d

        for ds in config.datasources:
            hostHeader = lookup_cwregion(ds.params['region'])
            httpRequest['MetricName'] = ds.datasource
            httpRequest['Namespace'] = ds.params['namespace']
            httpRequest['Dimensions.member.1.Name'] = ds.params['result_component_key']
            httpRequest['Dimensions.member.1.Value'] = ds.component
            awsKeys = (accesskey, secretkey)

            getURL = awsUrlSign(httpVerb,
                        hostHeader,
                        uriRequest,
                        httpRequest,
                        awsKeys)

            getURL = 'http://%s' % getURL
            backoff = backoff + .01
            log.debug('Backoff is %s for URL %s' % (backoff, getURL))
            result = yield getPage(getURL)
            pause = yield sleep(backoff)
            result = result.replace("\n", "")
            results.append((ds.component, ds.datasource, result))

        defer.returnValue(results)

    def onSuccess(self, results, config):

        resultTree = {}

        for result in results:
            valueMatch = re.search('<Maximum>(.*)</Maximum>', result[2])
            timeMatch = re.search('<Timestamp>(.*)</Timestamp>', result[2])
            datapoint = result[1]

            if valueMatch:
                if timeMatch:
                    try:
                        timeValue = calendar.timegm(
                                time.strptime(timeMatch.group(1), '%Y-%m-%dT%H:%M:%SZ')
                                )
                    except:
                        timeValue = calendar.timegm(datetime.datetime.utcnow().timetuple())
                else:
                    timeValue = calendar.timegm(datetime.datetime.utcnow().timetuple())

                resultTree[result[0]] = {'Value': valueMatch.group(1),
                                        'Datapoint': datapoint,
                                        'Time': timeValue}

        data = self.new_data()
        for instanceID in resultTree:
            component_id = instanceID
            datapoint = resultTree[instanceID]['Datapoint']
            timestamp = resultTree[instanceID]['Time']
            metricvalue = resultTree[instanceID]['Value']

            data['values'][component_id][datapoint] = \
                        (metricvalue, timestamp)

        data['events'].append({
            'eventClassKey': 'AWSCloudWatchSuccess',
            'eventKey': 'awsCloudWatchCollection',
            'summary': 'AWS CloudWatch: successful metrics collection',
            'device': config.id
            })

        return data

    def onError(self, result, config):
        errmsg = 'AWS: %s' % result_errmsg(result)

        log.error('%s %s', config.id, errmsg)

        data = self.new_data()
        data['events'].append({
            'eventClassKey': 'AWSCloudWatchError',
            'eventKey': 'awsCloudWatchCollection',
            'summary': errmsg,
            'device': config.id,
            })

        return data

