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

from twisted.internet.defer import inlineCallbacks, returnValue

from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.Zuul.interfaces import IRRDDataSourceInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSource, PythonDataSourcePlugin


class SQSDataSource(PythonDataSource):
    '''
    Datasource used to capture messages from SQS queues as events
    '''

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
    region = schema.TextLine(group=_t('Amazon'), title=_t('Region'))

class SQSDataSourceInfo(RRDDataSourceInfo):
    implements(ISQSDataSourceInfo)
    adapts(SQSDataSource)

    region = ProxyProperty('region')


class SQSDataSourcePlugin(PythonDataSourcePlugin):
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
    )

    @inlineCallbacks
    def collect(self, config):
        if False: yield
        returnValue(True)

    def onSuccess(self, result, config):
        print 'SUCCESS! ' * 100
        ds0 = config.datasources[0]
        accesskey = ds0.ec2accesskey
        secretkey = ds0.ec2secretkey
        print '>' * 30, ds0

        results = {'events': [], 'values': {}}

        for ds in config.datasources:
            print '>' * 50, ds.params
        '''

        sqsconnection = boto.sqs.connect_to_region(region.name, **credentials)    

        for queue in sqsconnection.get_all_queues():
            q_scheme = vars(queue)
            q_scheme['messages'] = map(vars, queue.get_messages())
            region_scheme[queue.id] = q_scheme
        '''
        results['events'].append({
            'summary': 'successful collection',
            'eventKey': 'SQSDataSource_result',
            'severity': 0,
        })
        return results

    def onError(self, result, config):
        """
        You can omit this method if you want the error result of the collect
        method to be used without further processing. It recommended to
        implement this method to capture errors.
        """
        print '!' * 300
        print result
        return {
            'events': [{
                'summary': 'error: %s' % result,
                'eventKey': 'SQSDataSource_result',
                'severity': 4,
            }],
        }
