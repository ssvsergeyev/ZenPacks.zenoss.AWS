######################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

import boto
import boto.vpc
import boto.ec2

from logging import getLogger
log = getLogger('zen.python')

from boto.ec2.connection import EC2Connection
from boto.s3.connection import S3Connection
from boto.vpc import VPCConnection
from twisted.internet import defer

from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin


class AWSBasePlugin(PythonDataSourcePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS components.
    """
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
    )

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

            data['values'][ds.component] = dict(
                keys_count=(len(keys), 'N'),
                total_size=(sum([key.size for key in keys]), 'N'),
            )

        defer.returnValue(data)


class EC2RegionPlugin(AWSBasePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS EC2Region soft limits.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        instance_filters = {
            'instance-state-name': [
                'pending',
                'running',
                'shutting-down',
                'stopping',
                'stopped',
            ],
        }

        for ds in config.datasources:
            ec2regionconn = boto.ec2.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )
            vpcregionconn = boto.vpc.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )

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
                instances_count=(instances_count, 'N'),
                elastic_ips_count=(elastic_ips_count, 'N'),
                subnets_count=(subnets_count, 'N'),
                volumes_count=(volumes_count, 'N'),
                vpc_security_groups_count=(sg_count, 'N'),
                vpc_security_rules_count=(rules_count, 'N')
            )
        print "==" * 20
        print data
        defer.returnValue(data)


class EC2VPCSubnetPlugin(AWSBasePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS VPC Subnets.
    """

    @classmethod
    def params(cls, datasource, context):
        return {
            'region': datasource.talesEval(datasource.region, context),
        }

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        for ds in config.datasources:
            region = ds.params['region']
            vpcregionconn = boto.vpc.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )
            subnet = yield vpcregionconn.get_all_subnets(ds.component).pop()

            data['values'][ds.component] = dict(
                available_ip_address_count=(
                    subnet.available_ip_address_count, 'N'
                )
            )

        defer.returnValue(data)