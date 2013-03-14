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
import re

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
    import awsUrlSign, result_errmsg, lookup_cwregion


class AmazonCloudWatchDataSource(PythonDataSource):
    '''
    Datasource used to capture datapoints from Amazon CloudWatch.
    '''

    ZENPACKID = 'ZenPacks.zenoss.AWS'

    sourcetypes = ('Amazon CloudWatch',)
    sourcetype = sourcetypes[0]

    plugin_classname = 'ZenPacks.zenoss.AWS.datasources.AmazonCloudWatchDataSource.AmazonCloudWatchDataSourcePlugin'

    region = ''
    namespace = ''
    dimension = ''

    _properties = PythonDataSource._properties + (
        {'id': 'region', 'type': 'string'},
        {'id': 'namespace', 'type': 'string'},
        {'id': 'dimension', 'type': 'string'},
        )


class IAmazonCloudWatchDataSourceInfo(IRRDDataSourceInfo):
    '''
    API Info interface for AmazonCloudWatchDataSource.
    '''

    namespace = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Namespace'))

    region = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Region'))

    dimension = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Dimension (i.e. InstanceId=${here/id})'))


class AmazonCloudWatchDataSourceInfo(RRDDataSourceInfo):
    '''
    API Info adapter factory for AmazonCloudWatchDataSource.
    '''

    implements(IAmazonCloudWatchDataSourceInfo)
    adapts(AmazonCloudWatchDataSource)

    testable = False

    cycletime = ProxyProperty('cycletime')

    region = ProxyProperty('region')
    namespace = ProxyProperty('namespace')
    dimension = ProxyProperty('dimension')


def timestamp_from_cloudwatch(cloudwatch_time_string):
    try:
        return calendar.timegm(
            time.strptime(cloudwatch_time_string, '%Y-%m-%dT%H:%M:%SZ'))

    except Exception:
        pass

    return calendar.timegm(datetime.datetime.utcnow().timetuple())


class AmazonCloudWatchDataSourcePlugin(PythonDataSourcePlugin):
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
        )

    @classmethod
    def config_key(cls, datasource, context):
        return(
            context.device().id,
            datasource.getCycleTime(context),
            datasource.rrdTemplate().id,
            datasource.id,
            datasource.plugin_classname,
            )

    @classmethod
    def params(cls, datasource, context):
        return {
            'region': datasource.talesEval(datasource.region, context),
            'namespace': datasource.talesEval(datasource.namespace, context),
            'dimension': datasource.talesEval(datasource.dimension, context),
            }

    @inlineCallbacks
    def collect(self, config):
        results = []

        ds0 = config.datasources[0]

        # Static for performance collection
        httpVerb = 'GET'
        uriRequest = '/'

        baseRequest = {}
        baseRequest['Action'] = 'GetMetricStatistics'
        baseRequest['StartTime'] = (
            datetime.datetime.utcnow() -
            datetime.timedelta(
                seconds=ds0.cycletime + 59)).strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z')

        baseRequest['EndTime'] = datetime.datetime.utcnow().strftime(
            '%Y-%m-%dT%H:%M:%S.000Z')

        baseRequest['Period'] = ds0.cycletime
        baseRequest['SignatureMethod'] = 'HmacSHA256'
        baseRequest['SignatureVersion'] = '2'
        baseRequest['Version'] = '2010-08-01'

        backoff = 0

        def sleep(secs):
            d = defer.Deferred()
            reactor.callLater(secs, d.callback, None)
            return d

        for ds in config.datasources:
            hostHeader = lookup_cwregion(ds.params['region'])

            httpRequest = baseRequest.copy()
            httpRequest['MetricName'] = ds.datasource
            httpRequest['Namespace'] = ds.params['namespace']

            dim_name, dim_value = ds.params['dimension'].split('=')

            httpRequest['Dimensions.member.1.Name'] = dim_name
            httpRequest['Dimensions.member.1.Value'] = dim_value
            httpRequest['Statistics.member.1'] = 'Average'

            getURL = awsUrlSign(
                httpVerb,
                hostHeader,
                uriRequest,
                httpRequest,
                (ds0.ec2accesskey, ds0.ec2secretkey))

            getURL = 'http://%s' % getURL
            backoff = backoff + .01
            log.debug('Backoff is %s for URL %s' % (backoff, getURL))
            result = yield getPage(getURL)
            pause = yield sleep(backoff)
            result = result.replace("\n", "")
            results.append((ds, result))

        defer.returnValue(results)

    def onSuccess(self, results, config):
        data = self.new_data()

        for datasource, result in results:
            valueMatch = re.search(r'<Average>(.*)</Average>', result)
            if not valueMatch:
                continue

            timeMatch = re.search(r'<Timestamp>(.*)</Timestamp>', result)
            if not timeMatch:
                continue

            timeValue = timestamp_from_cloudwatch(timeMatch.group(1))

            data['values'][datasource.component][datasource.datasource] = (
                valueMatch.group(1), timeValue)

        data['events'].append({
            'device': config.id,
            'summary': 'AWS CloudWatch: successful metrics collection',
            'severity': ZenEventClasses.Clear,
            'eventKey': 'awsCloudWatchCollection',
            'eventClassKey': 'AWSCloudWatchSuccess',
            })

        return data

    def onError(self, result, config):
        errmsg = 'AWS: %s' % result_errmsg(result)

        log.error('%s %s', config.id, errmsg)

        data = self.new_data()
        data['events'].append({
            'device': config.id,
            'summary': errmsg,
            'severity': ZenEventClasses.Error,
            'eventKey': 'awsCloudWatchCollection',
            'eventClassKey': 'AWSCloudWatchError',
            })

        return data
