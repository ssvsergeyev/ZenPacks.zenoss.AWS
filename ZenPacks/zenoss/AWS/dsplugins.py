######################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

from logging import getLogger
log = getLogger('zen.python')

import time
import boto
import boto.sqs
import boto.ec2
from boto.ec2.connection import EC2Connection
from boto.s3.connection import S3Connection
from boto.vpc import VPCConnection
from twisted.internet import defer

from Products.ZenUtils.Utils import prepId
from Products.ZenEvents import ZenEventClasses
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin


class AWSBasePlugin(PythonDataSourcePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS components.
    """
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
    )

    @classmethod
    def params(cls, datasource, context):
        try:
            region = datasource.talesEval(datasource.region, context)
        except:
            return {}
        return {
            'region': region,
        }

    @defer.inlineCallbacks
    def collect(self, config):
        pass

    def onSuccess(self, result, config):
        for component in result["values"].keys():
            result['events'].insert(0, {
                'component': component,
                'summary': 'Monitoring ok',
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': 0,
            })
        return result

    def onError(self, result, config):
        log.error(result)
        return {
            'vaues': {},
            'events': [{
                'summary': 'error: %s' % result,
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': 4,
            }],
            'maps': [],
        }


class S3BucketPlugin(AWSBasePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS S3Buckets.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        for ds in config.datasources:
            s3connection = S3Connection(ds.ec2accesskey, ds.ec2secretkey)
            bucket = s3connection.get_bucket(ds.component)
            keys = yield bucket.get_all_keys()

            t = time.time()
            data['values'][ds.component] = dict(
                keys_count=(len(keys), t),
                total_size=(sum([key.size for key in keys]), t),
            )

        defer.returnValue(data)


class EC2RegionPlugin(AWSBasePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS EC2Region soft limits.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        t = time.time()
        instance_filters = {
            'instance-state-name': [
                'pending',
                'running',
                'shutting-down',
                'stopping',
                'stopped',
            ],
        }
        accesskey = config.datasources[0].ec2accesskey
        secretkey = config.datasources[0].ec2secretkey

        ec2conn = EC2Connection(accesskey, secretkey)
        regions = yield ec2conn.get_all_regions()
        for region in regions:
            region_id = prepId(region.name)
            ec2regionconn = EC2Connection(accesskey, secretkey, region=region)
            vpcregionconn = VPCConnection(accesskey, secretkey, region=region)

            for ds in config.datasources:
                if ds.component == region_id:
                    instances_count = len(ec2regionconn.get_all_instances(
                        filters=instance_filters
                    ))
                    elastic_ips_count = len(ec2regionconn.get_all_addresses())
                    subnets_count = len(vpcregionconn.get_all_subnets())
                    volumes_count = len(ec2regionconn.get_all_volumes())
                    sg = ec2regionconn.get_all_security_groups()
                    sg_count = len(sg)
                    rules_count = 0
                    for group in sg:
                        rules_count = max(len(group.rules), rules_count)

                    data['values'][ds.component] = dict(
                        instances_count=(instances_count, t),
                        elastic_ips_count=(elastic_ips_count, t),
                        subnets_count=(subnets_count, t),
                        volumes_count=(volumes_count, t),
                        vpc_security_groups_count=(sg_count, t),
                        vpc_security_rules_count=(rules_count, t)
                    )

        defer.returnValue(data)


class SQSQueuePlugin(AWSBasePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS SQSQueue.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        for ds in config.datasources:
            region = ds.params['region']
            sqsconnection = yield boto.sqs.connect_to_region(
                region,
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
        defer.returnValue(data)


class ZonePlugin(AWSBasePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS Zone.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        for ds in config.datasources:
            region = ds.params['region']
            ec2regionconn = boto.ec2.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey
            )
            zone = yield ec2regionconn.get_all_zones(ds.component).pop()
            if not zone.state == 'available':
                severity = ZenEventClasses.Warning
            else:
                severity = ZenEventClasses.Clear

                data['events'].append({
                    'summary': 'Zone state is {0}'.format(zone.state),
                    'component': ds.component,
                    'eventKey': 'ZoneStatus',
                    'severity': severity,
                    'eventClass': '/Status',
                })
        defer.returnValue(data)
