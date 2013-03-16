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
    import awsUrlSign, iso8601, result_errmsg, lookup_cwregion


MAX_RETRIES = 3


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
            datasource.getRegionId(),
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

        # CloudWatch only accepts periods that are evenly divisible by 60.
        cycletime = (ds0.cycletime / 60) * 60

        # Static for performance collection
        httpVerb = 'GET'
        uriRequest = '/'

        baseRequest = {}
        baseRequest['Action'] = 'GetMetricStatistics'
        baseRequest['SignatureMethod'] = 'HmacSHA256'
        baseRequest['SignatureVersion'] = '2'
        baseRequest['Version'] = '2010-08-01'
        baseRequest['Period'] = cycletime
        baseRequest['Statistics.member.1'] = 'Average'

        def sleep(secs):
            d = defer.Deferred()
            reactor.callLater(secs, d.callback, None)
            return d

        for ds in config.datasources:
            hostHeader = lookup_cwregion(ds.params['region'])

            httpRequest = baseRequest.copy()
            httpRequest['StartTime'] = iso8601(seconds_ago=(cycletime * 2))
            httpRequest['EndTime'] = iso8601()
            httpRequest['MetricName'] = ds.datasource
            httpRequest['Namespace'] = ds.params['namespace']

            if ds.params['dimension']:
                dim_name, dim_value = ds.params['dimension'].split('=')

                httpRequest['Dimensions.member.1.Name'] = dim_name
                httpRequest['Dimensions.member.1.Value'] = dim_value

            getURL = awsUrlSign(
                httpVerb,
                hostHeader,
                uriRequest,
                httpRequest,
                (ds0.ec2accesskey, ds0.ec2secretkey))

            getURL = 'http://%s' % getURL

            # Incremental backoff as outlined by AWS.
            # http://aws.amazon.com/articles/1394
            for retry in xrange(MAX_RETRIES + 1):
                if retry > 0:
                    delay = (random.random() * pow(4, retry)) / 10.0
                    log.debug('retry %s: backoff is %s seconds', retry, delay)
                    wait = yield sleep(delay)

                try:
                    log.debug('requesting: %s', getURL)
                    result = yield getPage(getURL)

                except Exception, ex:
                    code = getattr(ex, 'status', None)
                    if code in ('500', '503'):
                        continue

                    raise

                else:
                    result = result.replace("\n", "")
                    results.append((ds, result))
                    break

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
