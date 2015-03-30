##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.AWS')
logging.getLogger('boto').setLevel(logging.CRITICAL)

import datetime

from twisted.internet import defer, threads, reactor

reactor.suggestThreadPoolSize(30)

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

from ZenPacks.zenoss.AWS.utils import result_errmsg

from ZenPacks.zenoss.AWS.utils import addLocalLibPath

addLocalLibPath()

import boto.ec2.cloudwatch


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


class AmazonCloudWatchDataSourcePlugin(PythonDataSourcePlugin):
    '''
    Datasource plugin for PythonCollector
    '''

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

    def _do_collect(self, config):
        '''
        Worker, do actual data retrieval
        '''
        log.debug("Collect for AWS")

        data = self.new_data()
        ds0 = config.datasources[0]
        accesskey = ds0.ec2accesskey
        secretkey = ds0.ec2secretkey

        # CloudWatch only accepts periods that are evenly divisible by 60.
        cycletime = (ds0.cycletime / 60) * 60

        for ds in config.datasources:
            region = ds.params['region']
            region_con = boto.ec2.cloudwatch.connect_to_region(region,
                aws_access_key_id=accesskey,
                aws_secret_access_key=secretkey
            )

            dimensions = {}
            if ds.params['dimension']:
                dim_group = ds.params['dimension'].split(';')
                for k, v in [x.split('=') for x in dim_group]:
                    dimensions[k] = v

            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(seconds=cycletime * 2)

            try:
                res = region_con.get_metric_statistics(
                    period=cycletime,
                    start_time=start_time,
                    end_time=end_time,
                    metric_name=ds.params['metric'],
                    namespace=ds.params['namespace'],
                    statistics=[ds.params['statistic']],
                    dimensions=dimensions
                )

                if res:
                    value = float(res[-1][ds.params['statistic']])
                    data['values'][ds.component][ds.datasource] = value, 'N'
            except Exception, ex:
                code = getattr(ex, 'status', None)
                body = getattr(ex, 'body', '')
                if 'throttling' in body.lower():
                    data['events'].append({
                        'device': config.id,
                        'summary': 'AWS CloudWatch: Rate exceeded. '
                            'Consider to contact AWS support with request '
                            'to increase CloudWatch API limits.',
                        'severity': ZenEventClasses.Info,
                        'eventKey': 'awsCloudWatchCollectionThrottling',
                        'eventClassKey': 'AWSCloudWatchThrottling',
                        'eventClass': '/AWS/Suggestion',
                        })
                if code in ('500', '503'):
                    continue

        return data

    def collect(self, config):
        '''
        Retrieves metrics data from CloudWatch
        '''
        return threads.deferToThread(lambda: self._do_collect(config))
        # return defer.maybeDeferred(lambda: self._do_collect(config))

    def onSuccess(self, results, config):
        '''
        Successful collection
        '''

        results['events'].append({
            'device': config.id,
            'summary': 'AWS CloudWatch: successful metrics collection',
            'severity': ZenEventClasses.Clear,
            'eventKey': 'awsCloudWatchCollection',
            'eventClassKey': 'AWSCloudWatchSuccess',
            })
        return results

    def onError(self, result, config):
        '''
        In case we error(s) occured during collection
        '''

        errmsg = 'AWS: %s' % result_errmsg(result)
        data = self.new_data()

        log.error('%s: %s', config.id, errmsg)
        data['events'].append({
            'device': config.id,
            'summary': errmsg,
            'severity': ZenEventClasses.Error,
            'eventKey': 'awsCloudWatchCollection',
            'eventClassKey': 'AWSCloudWatchError',
            })

        return data
