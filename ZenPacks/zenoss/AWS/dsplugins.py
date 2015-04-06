######################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

import re
from logging import getLogger
log = getLogger('zen.python')

import boto
import boto.ec2
import boto.sqs
import boto.vpc

from boto.sqs.message import RawMessage
from boto.s3.connection import S3Connection
from twisted.internet import defer, threads

from Products.DataCollector.plugins.DataMaps import ObjectMap
from Products.ZenEvents import ZenEventClasses
from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin

from ZenPacks.zenoss.AWS.utils import unreserved_instance_count
from ZenPacks.zenoss.AWS.utils import unused_reserved_instances_count

from ZenPacks.zenoss.AWS.modeler.plugins.aws.EC2 import instances_rm
from ZenPacks.zenoss.AWS.modeler.plugins.aws.EC2 import INSTANCE_FILTERS


class AWSBasePlugin(PythonDataSourcePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS components.
    """
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
    )
    component = None

    @classmethod
    def params(cls, datasource, context):
        try:
            region = datasource.talesEval(datasource.region, context)
        except:
            return {}
        return {
            'region': region,
        }

    def onSuccess(self, result, config):
        for component in result["values"].keys():
            result['events'].insert(0, {
                'component': component,
                'summary': 'Monitoring ok',
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': ZenEventClasses.Clear,
            })
        return result

    def onError(self, result, config):
        data = self.new_data()
        str_res = str(result)
        eventKey = 'aws_result'
        if not self.component:
            eventKey = 'aws_bucket_result'
        if "<Message>" in str_res and self.component:
            m = re.search('<Message>(.+?)</Message>', str_res)
            if m:
                res = m.group(1)
                log.info(res)
                if self.component in str_res:
                    data['events'].append({
                        'component': self.component,
                        'summary': res,
                        'eventClass': '/Status',
                        'eventKey': 'aws_result',
                        'severity': ZenEventClasses.Info,
                    })
                    return data
        else:
            if 'IndexError' in str(result.type):
                summary = 'The component {0} does not exist.'.format(
                    self.component
                )
                severity = ZenEventClasses.Info
            elif ('timed out' in str_res) or ("name resolution" in str_res) or\
                 ("service not known" in str_res) or\
                 ("argument of type 'int' is not iterable" in str_res):
                summary = "Connection timed out or network problems."
                severity = ZenEventClasses.Error
            else:
                summary = str_res
                severity = ZenEventClasses.Error

            data['events'].append({
                'component': self.component,
                'summary': summary,
                'eventClass': '/Status',
                'eventKey': eventKey,
                'severity': severity,
            })
            return data


class S3BucketPlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS S3Buckets.
    """

    def inner(self, config):
        data = self.new_data()
        ds0 = config.datasources[0]
        bucket_keys = {}
        # Add support Signature V4 for 's3' into boto config
        if not boto.config.get('s3', 'use-sigv4'):
            boto.config.add_section('s3')
            boto.config.set('s3', 'use-sigv4', 'True')
        s3connection = S3Connection(
            ds0.ec2accesskey, ds0.ec2secretkey,
            host=S3Connection.DefaultHost
        )
        buckets = s3connection.get_all_buckets()
        data['events'].append({
            'summary': 'Monitoring ok',
            'eventClass': '/Status',
            'eventKey': 'aws_bucket_result',
            'severity': ZenEventClasses.Clear,
        })

        for bucket in buckets:
            name = bucket.name
            try:
                bucket_keys.update({name: bucket.get_all_keys()})
            except Exception, e:
                if isinstance(e, boto.exception.S3ResponseError):
                    # Parse an exception message to find expected 'region'
                    pattern = (
                        "The authorization header is malformed; the "
                        "region '[\w-]+' is wrong; expecting '([\w-]+)'"
                    )
                    m = re.match(pattern, e.message)
                    if m:
                        region = m.group(1)
                        region_con = boto.s3.connect_to_region(
                            region, aws_access_key_id=ds0.ec2accesskey,
                            aws_secret_access_key=ds0.ec2secretkey
                        )
                        bucket = region_con.get_bucket(name)
                        bucket_keys.update({name: bucket.get_all_keys()})
                    else:
                        bucket_keys.update({name: e})
                    continue
                else:
                    if "argument of type 'int' is not iterable" in str(e):
                        # TODO: find the reason why 'boto' has that behavior in this case
                        continue
                    bucket_keys.update({name: e})
                    continue
        for ds in config.datasources:
            self.component = ds.component
            keys = bucket_keys.get(ds.component) or []
            if not isinstance(keys, list):
                data['events'].append({
                    'component': self.component,
                    'summary': str(keys),
                    'eventClass': '/Status',
                    'eventKey': 'aws_result',
                    'severity': ZenEventClasses.Error,
                })
                continue
            data['values'][ds.component] = dict(
                keys_count=(len(keys), 'N'),
                total_size=(sum([key.size for key in keys]), 'N'),
            )
        return data

    def collect(self, config):
        return threads.deferToThread(lambda: self.inner(config))


class EC2RegionPlugin(AWSBasePlugin):
    """
    Retrieves information about soft limits for region
    and updates statuses of EC2 instances and volumes.
    """

    proxy_attributes = (
        'ec2accesskey',
        'ec2secretkey',
        'zAWSDiscover',
        'zAWSRegionPEM',
        'zAWSRemodelEnabled',
        'getDiscoverGuests',
    )

    def collect(self, config):
        def inner():
            data = self.new_data()
            instance_states = {}
            for ds in config.datasources:
                region_id = self.component = ds.component
                ec2regionconn = boto.ec2.connect_to_region(
                    region_id,
                    aws_access_key_id=ds.ec2accesskey,
                    aws_secret_access_key=ds.ec2secretkey,
                )
                vpcregionconn = boto.vpc.connect_to_region(
                    region_id,
                    aws_access_key_id=ds.ec2accesskey,
                    aws_secret_access_key=ds.ec2secretkey,
                )

                instances = ec2regionconn.get_only_instances(
                    filters=INSTANCE_FILTERS
                )
                volumes = ec2regionconn.get_all_volumes()

                elastic_ips_count = len(ec2regionconn.get_all_addresses())
                subnets_count = len(vpcregionconn.get_all_subnets())
                sg = ec2regionconn.get_all_security_groups()
                sg_count = len(sg)
                rules_count = 0
                for group in sg:
                    rules_count = max(len(group.rules), rules_count)

                data['values'][region_id] = dict(
                    instances_count=(len(instances), 'N'),
                    elastic_ips_count=(elastic_ips_count, 'N'),
                    subnets_count=(subnets_count, 'N'),
                    volumes_count=(len(volumes), 'N'),
                    vpc_security_groups_count=(sg_count, 'N'),
                    vpc_security_rules_count=(rules_count, 'N')
                )

                # Previously zAWSRemodelEnabled was a string, fix for this case
                if str(ds.zAWSRemodelEnabled).lower() == 'true':
                    data['maps'].append(instances_rm(
                        region_id,
                        ds,
                        instances,
                        [],
                        instance_states,
                        ec2regionconn
                    ))
                else:
                    # InstanceState moved here for optimization
                    ins_res = {}
                    for instance in instances:
                        ins_res[prepId(instance.id)] = instance.state
                    data['maps'].append(ObjectMap({
                        "compname": "regions/%s" % region_id,
                        "modname": "Instances states",
                        "setInstancesStates": ins_res
                    }))

                # VolumeState moved here for optimization
                vol_res = {}
                for volume in volumes:
                    vol_res[prepId(volume.id)] = volume.status
                data['maps'].append(ObjectMap({
                    "compname": "regions/%s" % region_id,
                    "modname": "Volumes states",
                    "setVolumesStatuses": vol_res
                }))

            ds0 = config.datasources[0]
            if str(ds0.zAWSRemodelEnabled).lower() == 'true':
                # Run "setDiscoverGuests" every time during the monitoring
                data['maps'].append(ObjectMap({
                    "modname": "Guest update",
                    "setDiscoverGuests": False if ds0.getDiscoverGuests
                    else True,
                }))
            return data

        return threads.deferToThread(inner)


def get_messages(queue):
    messages = {}
    message_count = -1
    while message_count < len(messages):
        message_count = len(messages)
        res = queue.get_messages(num_messages=10, visibility_timeout=3)
        for message in res:
            messages[message.id] = message._body
    return messages


class SQSQueuePlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS SQSQueue.
    """

    def collect(self, config):
        def inner():
            data = self.new_data()
            for ds in config.datasources:
                self.component = ds.component
                name = ds.component[len('queue_'):]
                region = ds.params['region']
                sqsconnection = boto.sqs.connect_to_region(
                    region,
                    aws_access_key_id=ds.ec2accesskey,
                    aws_secret_access_key=ds.ec2secretkey,
                )
                queue = sqsconnection.get_queue(name)
                if queue:
                    queue.set_message_class(RawMessage)
                    messages = get_messages(queue)

                    data['events'].append({
                        'component': self.component,
                        'summary': "Monitoring ok",
                        'eventClass': '/Status',
                        'eventKey': 'aws_result',
                        'severity': ZenEventClasses.Clear,
                    })

                    for id, text in messages.iteritems():
                        data['events'].append({
                            'summary': text,
                            'device': config.id,
                            'component': self.component,
                            'eventKey': id,
                            'severity': ZenEventClasses.Info,
                            'eventClass': '/AWS/SQSMessage',
                        })
                else:
                    data['events'].append({
                        'summary': 'Queue "%s" does not exist' % name,
                        'device': config.id,
                        'component': self.component,
                        'severity': ZenEventClasses.Info,
                        'eventClass': '/Status',
                    })
            return data

        return threads.deferToThread(inner)


class ZonePlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS Zone.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
        for ds in config.datasources:
            self.component = ds.component
            region = ds.params['region']
            ec2regionconn = boto.ec2.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey
            )
            zone = yield ec2regionconn.get_all_zones(ds.component).pop()
            if zone.state == 'available':
                severity = ZenEventClasses.Clear
                data['events'].append({
                    'summary': "Monitoring Ok",
                    'component': ds.component,
                    'severity': severity,
                    'eventKey': 'aws_result',
                    'eventClass': '/Status',
                })
            else:
                severity = ZenEventClasses.Warning
            data['events'].append({
                'summary': 'Zone state is {0}'.format(zone.state),
                'component': ds.component,
                'eventKey': 'ZoneStatus',
                'severity': severity,
                'eventClass': '/Status',
            })

            data['maps'].append(ObjectMap({
                "compname": "regions/%s/zones/%s" % (
                    region, ds.component),
                "modname": "Zone state",
                "state": zone.state
            }))
        defer.returnValue(data)


class EC2VPCSubnetPlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS VPC Subnets.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
        for ds in config.datasources:
            self.component = ds.component
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

            data['maps'].append(ObjectMap({
                "compname": "regions/%s/vpc_subnets/%s" % (
                    region, ds.component),
                "modname": "Subnet state",
                "state": subnet.state
            }))

        defer.returnValue(data)

CONNECTION_TYPE = {
    'EC2VPC': 'vpc',
    'EC2Snapshot': 'ec2',
    'EC2Volume': 'ec2',
    'VPNGateway': 'vpc',
    'EC2Image': 'ec2',
    'EC2Instance': 'ec2',
    'EC2Instance-Detailed': 'ec2',
    # 'EC2Instance-Custom': 'ec2',
}


# Plugins for components' state remodeling.
class EC2BaseStatePlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS components' states.
    """
    ec2regionconn = None
    vpcregionconn = None

    def connect_to_region(self, ds):
        region = ds.params['region']
        creds = dict(
            aws_access_key_id=ds.ec2accesskey,
            aws_secret_access_key=ds.ec2secretkey,
        )
        if CONNECTION_TYPE.get(ds.template) == 'ec2':
            self.ec2regionconn = boto.ec2.connect_to_region(
                region, **creds
            )
        else:
            self.vpcregionconn = boto.vpc.connect_to_region(
                region, **creds
            )

    def results_to_maps(self, region, component):
        """Return Object map for the component status remodeling.  """

    def gen_events(self, ds, data):
        """ Generate the events.  """

    def inner(self, config):
        data = self.new_data()
        for ds in config.datasources:
            self.component = ds.component
            self.connect_to_region(ds)

            maps = self.results_to_maps(ds.params['region'], ds.component)
            if maps:
                data['maps'].append(maps)

            self.gen_events(ds, data)

        return data

    def collect(self, config):
        return threads.deferToThread(lambda: self.inner(config))


class EC2VPCStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS VPC state.
    """

    def results_to_maps(self, region, component):
        vpc = self.vpcregionconn.get_all_vpcs(component).pop()
        return ObjectMap({
            "compname": "regions/%s/vpcs/%s" % (
                region, component),
            "modname": "VPC state",
            "state": vpc.state
        })


class VPNGatewayStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS Gateways state.
    """

    def results_to_maps(self, region, component):
        gateway = self.vpcregionconn.get_all_vpn_gateways(component).pop()
        return ObjectMap({
            "compname": "regions/%s/vpn_gateways/%s" % (
                region, component),
            "modname": "VPNGateway state",
            "state": gateway.state
        })


class EC2UnreservedInstancesPlugin(AWSBasePlugin):
    """
    Subclass of EC2BaseStatePlugin to check if instance could be reserved
    """

    def inner(self, config):
        data = self.new_data()
        for ds in config.datasources:
            self.component = ds.component
            region = ds.params['region']
            ec2_conn = boto.ec2.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )
            instance = ec2_conn.get_only_instances(ds.component).pop()
            c = unreserved_instance_count(ec2_conn, instance)

            event = None
            if c == 1:
                event = 'This instance could be reserved'
            elif c > 1:
                event = 'There are {0} instances of this type in this ' \
                    'availability zone which could be reserved'.format(c)

            if event:
                data['events'].append({
                    'summary': event,
                    'device': config.id,
                    'component': ds.component,
                    'severity': ZenEventClasses.Info,
                    'eventClass': '/AWS/Suggestion',
                })
        return data

    def collect(self, config):
        return threads.deferToThread(lambda: self.inner(config))


class EC2UnusedReservedInstancesPlugin(AWSBasePlugin):

    def inner(self, config):
        data = self.new_data()
        for ds in config.datasources:
            self.component = ds.component
            region = ds.params['region']
            ec2_conn = boto.ec2.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )

            reserved_instance = ec2_conn.get_all_reserved_instances(
                ds.component
            ).pop()

            c = unused_reserved_instances_count(
                ec2_conn,
                reserved_instance
            )

            event = None
            if c == 1:
                event = 'This reserved instance is unused'
            elif c > 1:
                event = 'There are {0} unused reserved instances of ' \
                    'this type in this availability zone'.format(c)

            if event:
                data['events'].append({
                    'summary': event,
                    'device': config.id,
                    'component': ds.component,
                    'severity': ZenEventClasses.Info,
                    'eventClass': '/AWS/Suggestion',
                })
        return data

    def collect(self, config):
        return threads.deferToThread(lambda: self.inner(config))
