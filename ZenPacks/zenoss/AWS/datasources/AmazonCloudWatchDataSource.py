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
import os

from cStringIO import StringIO
from lxml import etree

from twisted.web import client as txwebclient
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

from ZenPacks.zenoss.AWS.utils import awsUrlSign, iso8601, result_errmsg,\
    lookup_cwregion, twisted_web_client_parse


MAX_RETRIES = 3

class ProxyWebClient(object):
    """web methods with proxy."""

    def __init__(self, url, username=None, password=None):
        # get scheme used by url
        scheme, host, port, path = twisted_web_client_parse(url)
        envname = '%s_proxy' % scheme
        self.use_proxy = False
        self.proxy_host = None
        self.proxy_port = None
        if envname in os.environ.keys():
            proxy = os.environ.get('%s_proxy' % scheme)
            if proxy:
                # using proxy server
                # host:port identifies a proxy server
                # url is the actual target
                self.use_proxy = True
                scheme, host, port, path = twisted_web_client_parse(proxy)
                self.proxy_host = host
                self.proxy_port = port
                self.username = username
                self.password = password
        else:
            self.host = host
            self.port = port
        self.path = url
        self.url = url

    def get_page(self, contextFactory=None, *args, **kwargs):
        scheme, _, _, _ = twisted_web_client_parse(self.url)
        factory = txwebclient.HTTPClientFactory(self.url)
        if scheme == 'https':
            from twisted.internet import ssl
            if contextFactory is None:
                contextFactory = ssl.ClientContextFactory()
            if self.use_proxy:
                reactor.connectSSL(self.proxy_host, self.proxy_port,
                               factory, contextFactory)
            else:
                reactor.connectSSL(self.host, self.port,
                               factory, contextFactory)
        else:
            if self.use_proxy:
                reactor.connectTCP(self.proxy_host, self.proxy_port, factory)
            else:
                reactor.connectTCP(self.host, self.port, factory)
        return factory.deferred.addCallbacks(self.getdata, self.errdata)

    def getdata(self, data):
        return data

    def errdata(self, failure):
        log.error('%s: %s', 'AWSCloudWatchError', failure.getErrorMessage())
        return failure.getErrorMessage()

class AmazonCloudWatchDataSource(PythonDataSource):
    '''
    Datasource used to capture datapoints from Amazon CloudWatch.
    '''

    ZENPACKID = 'ZenPacks.zenoss.AWS'

    sourcetypes = ('Amazon CloudWatch',)
    sourcetype = sourcetypes[0]

    # RRDDataSource
    component = '${here/id}'
    cycletime = 300

    # PythonDataSource
    plugin_classname = 'ZenPacks.zenoss.AWS.datasources.'\
        'AmazonCloudWatchDataSource.AmazonCloudWatchDataSourcePlugin'

    # AmazonCloudWatchDataSource
    namespace = ''
    metric = ''
    statistic = 'Average'
    dimension = '${here/getDimension}'
    region = '${here/getRegionId}'

    _properties = PythonDataSource._properties + (
        {'id': 'namespace', 'type': 'string'},
        {'id': 'metric', 'type': 'string'},
        {'id': 'statistic', 'type': 'string'},
        {'id': 'dimension', 'type': 'string'},
        {'id': 'region', 'type': 'string'},
        )


class IAmazonCloudWatchDataSourceInfo(IRRDDataSourceInfo):
    '''
    API Info interface for AmazonCloudWatchDataSource.
    '''

    namespace = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Namespace'))

    metric = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Metric Name'))

    statistic = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Statistic'))

    dimension = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Dimension'))

    region = schema.TextLine(
        group=_t('Amazon CloudWatch'),
        title=_t('Region'))


class AmazonCloudWatchDataSourceInfo(RRDDataSourceInfo):
    '''
    API Info adapter factory for AmazonCloudWatchDataSource.
    '''

    implements(IAmazonCloudWatchDataSourceInfo)
    adapts(AmazonCloudWatchDataSource)

    testable = False

    cycletime = ProxyProperty('cycletime')

    namespace = ProxyProperty('namespace')
    metric = ProxyProperty('metric')
    statistic = ProxyProperty('statistic')
    dimension = ProxyProperty('dimension')
    region = ProxyProperty('region')


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
            context.getRegionId(),
            datasource.namespace,
            context.getDimension(),
            )

    @classmethod
    def params(cls, datasource, context):
        return {
            'namespace': datasource.talesEval(datasource.namespace, context),
            'metric': datasource.talesEval(datasource.metric, context),
            'statistic': datasource.talesEval(datasource.statistic, context),
            'dimension': datasource.talesEval(datasource.dimension, context),
            'region': datasource.talesEval(datasource.region, context),
            }

    @inlineCallbacks
    def collect(self, config):
        # defer.returnValue([])

        log.debug("Collect for AWS")
        results = []

        ds0 = config.datasources[0]
        accesskey = ds0.ec2accesskey
        secretkey = ds0.ec2secretkey

        # CloudWatch only accepts periods that are evenly divisible by 60.
        cycletime = (ds0.cycletime / 60) * 60

        # Static for performance collection
        httpVerb = 'GET'
        uriRequest = '/'

        baseRequest = {}
        baseRequest['SignatureMethod'] = 'HmacSHA256'
        baseRequest['SignatureVersion'] = '2'

        def sleep(secs):
            d = defer.Deferred()
            reactor.callLater(secs, d.callback, None)
            return d

        for ds in config.datasources:
            hostHeader = lookup_cwregion(ds.params['region'])

            monitorRequest = baseRequest.copy()
            monitorRequest['Action'] = 'GetMetricStatistics'
            monitorRequest['Version'] = '2010-08-01'
            monitorRequest['Period'] = cycletime
            monitorRequest['StartTime'] = iso8601(seconds_ago=(cycletime * 2))
            monitorRequest['EndTime'] = iso8601()
            monitorRequest['Namespace'] = ds.params['namespace']
            monitorRequest['MetricName'] = ds.params['metric']
            monitorRequest['Statistics.member.1'] = ds.params['statistic']

            if ds.params['dimension']:
                dim_group = ds.params['dimension'].split(';')

                i = 0
                for dim_name, dim_value in [x.split('=') for x in dim_group]:
                    i += 1
                    monitorRequest['Dimensions.member.%d.Name' % i] = dim_name
                    monitorRequest['Dimensions.member.%d.Value' % i] = dim_value

            getURL = awsUrlSign(
                httpVerb,
                hostHeader,
                uriRequest,
                monitorRequest,
                (accesskey, secretkey))

            getURL = 'http://%s' % getURL
            factory = ProxyWebClient(getURL)

            # Incremental backoff as outlined by AWS.
            # http://aws.amazon.com/articles/1394
            for retry in xrange(MAX_RETRIES + 1):
                if retry > 0:
                    delay = (random.random() * pow(4, retry)) / 10.0
                    log.debug(
                        '%s (%s): retry %s backoff is %s seconds',
                        config.id, ds.params['region'], retry, delay)

                    wait = yield sleep(delay)

                try:
                    log.debug(
                        '%s (%s): requesting %s %s/%s for %s',
                        config.id,
                        ds.params['region'],
                        ds.params['statistic'],
                        ds.params['namespace'],
                        ds.params['metric'],
                        ds.params['dimension'] or 'region')

                    result = yield factory.get_page()

                except Exception, ex:
                    code = getattr(ex, 'status', None)
                    if code in ('500', '503'):
                        continue

                    raise

                else:
                    results.append((ds, result))
                    break

            # if ds.params['metric'] == 'VolumeTotalWriteTime':
            #     # Get Volume Status
            #     volumeRequest = baseRequest.copy()
            #     volumeRequest['Action'] = 'DescribeVolumeStatus'
            #     volumeRequest['Version'] = '2013-02-01'
            #     volumeRequest['VolumeId.1'] = dim_value
            #     hostHeader = 'ec2.amazonaws.com'

            #     getURL = awsUrlSign(
            #         httpVerb,
            #         hostHeader,
            #         uriRequest,
            #         volumeRequest,
            #         [accesskey, secretkey]
            #     )

            #     getURL = 'http://%s' % getURL

            #     log.debug('Get Volume Information: %s', getURL)

            #     result = yield getPage(getURL)
            #     results.append(('volumestatus', result))

        defer.returnValue(results)

    def onSuccess(self, results, config):
        data = self.new_data()

        for ds, result in results:

            # Only one namespace is used. Mangle the xmlns attribute
            # to make further processing of the XML simpler.
            result = result.replace(' xmlns=', ' xmlnamespace=', 1)

            try:
                stats = etree.parse(StringIO(result))
            except Exception:
                log.exception(
                    '%s (%s): error parsing response XML\n%s',
                    config.id, ds.params['region'], result)
                continue

            if ds == 'volumestatus':
                #Parse volume status events
                try:
                    volumes = stats.xpath('//volumeStatusSet/item')

                    for vol in volumes:
                        volumeID = str(vol.xpath('volumeId[last()]/text()')[0])
                        volumeStatus = str(vol.xpath(
                            'volumeStatus/status/text()'
                        )[0])

                        if volumeStatus == 'ok':
                            data['events'].append({
                                'component': volumeID,
                                'device': config.id,
                                'summary': 'AWS Volume Status: OK',
                                'severity': ZenEventClasses.Clear,
                                'eventClass': '/Status',
                                'eventClassKey': 'AWSVolume',
                            })
                        else:
                            data['events'].append({
                                'component': volumeID,
                                'device': config.id,
                                'summary': "AWS Volume Status: {}".format(
                                    volumeStatus
                                ),
                                'severity': ZenEventClasses.Critical,
                                'eventClass': '/Status',
                                'eventClassKey': 'AWSVolume',
                            })

                except IndexError:
                    continue

            else:
                #Parse cloudwatch metrics
                try:
                    timestamp = timestamp_from_cloudwatch(
                        stats.xpath('//Timestamp[last()]/text()')[0])

                    value = stats.xpath('//%s[last()]/text()' % (
                        ds.params['statistic']))[0]

                except IndexError:
                    # No value in response. This is usually normal.
                    value = 0
                    timestamp = 'N'
                    # continue

                data['values'][ds.component][ds.datasource] = value, 'N'  # timestamp
                # data['values'][ds.component][ds.datasource] = (value, timestamp)

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
        log.error('%s: %s', config.id, errmsg)

        data = self.new_data()
        data['events'].append({
            'device': config.id,
            'summary': errmsg,
            'severity': ZenEventClasses.Error,
            'eventKey': 'awsCloudWatchCollection',
            'eventClassKey': 'AWSCloudWatchError',
            })

        return data
