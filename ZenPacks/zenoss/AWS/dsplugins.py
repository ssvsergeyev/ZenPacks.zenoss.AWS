######################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
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
from twisted.internet import defer

from Products.DataCollector.plugins.DataMaps import ObjectMap
from Products.ZenEvents import ZenEventClasses
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin

from Products.ZenUtils.Utils import prepId

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
        if "<Message>" in str(result):
            result = str(result)
            m = re.search('<Message>(.+?)</Message>', result)
            if m:
                res = m.group(1)
                log.info(res)
                if self.component in result:
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
            else:
                summary = str(result)
                severity = ZenEventClasses.Error

            data['events'].append({
                'component': self.component,
                'summary': summary,
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': severity,

            })
            return data


class S3BucketPlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS S3Buckets.
    """

    def collect(self, config):
        def inner():
            data = self.new_data()
            for ds in config.datasources:
                self.component = ds.component
                s3connection = S3Connection(ds.ec2accesskey, ds.ec2secretkey)
                bucket = s3connection.get_bucket(ds.component)
                keys = bucket.get_all_keys()

                data['values'][ds.component] = dict(
                    keys_count=(len(keys), 'N'),
                    total_size=(sum([key.size for key in keys]), 'N'),
                )
            return data

        return defer.maybeDeferred(inner)


class EC2RegionPlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS EC2Region soft limits.
    """
    proxy_attributes = (
        'ec2accesskey',
        'ec2secretkey',
        'zAWSDiscover',
        'zAWSRegionPEM',
    )

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
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
            elastic_ips_count = len(ec2regionconn.get_all_addresses())
            subnets_count = len(vpcregionconn.get_all_subnets())
            volumes_count = len(ec2regionconn.get_all_volumes())
            sg = yield ec2regionconn.get_all_security_groups()
            sg_count = len(sg)
            rules_count = 0
            for group in sg:
                rules_count = max(len(group.rules), rules_count)

            data['values'][region_id] = dict(
                instances_count=(len(instances), 'N'),
                elastic_ips_count=(elastic_ips_count, 'N'),
                subnets_count=(subnets_count, 'N'),
                volumes_count=(volumes_count, 'N'),
                vpc_security_groups_count=(sg_count, 'N'),
                vpc_security_rules_count=(rules_count, 'N')
            )
            data['maps'].append(instances_rm(
                region_id,
                ds,
                instances,
                []
            ))

        defer.returnValue(data)

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
                        'summary': 'Queue "%s" does not exists' % name,
                        'device': config.id,
                        'component': self.component,
                        'severity': ZenEventClasses.Info,
                        'eventClass': '/Status',
                    })
            return data

        return defer.maybeDeferred(inner)


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

    def results_to_maps(self, region, component):
        """Return Object map for the component status remodeling.
        """
        pass

    def collect(self, config):
        def inner():
            data = self.new_data()
            for ds in config.datasources:
                self.component = ds.component
                region = ds.params['region']
                if CONNECTION_TYPE.get(ds.template) == 'ec2':
                    self.ec2regionconn = boto.ec2.connect_to_region(
                        region,
                        aws_access_key_id=ds.ec2accesskey,
                        aws_secret_access_key=ds.ec2secretkey,
                    )
                else:
                    self.vpcregionconn = boto.vpc.connect_to_region(
                        region,
                        aws_access_key_id=ds.ec2accesskey,
                        aws_secret_access_key=ds.ec2secretkey,
                    )

                maps = self.results_to_maps(region, ds.component)
                if maps:
                    data['maps'].append(maps)
            return data

        return defer.maybeDeferred(inner)


class EC2InstanceStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS Instance state.
    """

    def results_to_maps(self, region, component):
        if not self.ec2regionconn:
            return
        instance = self.ec2regionconn.get_only_instances(component).pop()
        return ObjectMap({
            "compname": "regions/%s/instances/%s" % (
                region, component),
            "modname": "Instance state",
            "state": instance.state
        })


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


class EC2SnapshotStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS Snapshot status.
    """

    def results_to_maps(self, region, component):
        snapshot = self.ec2regionconn.get_all_snapshots(component).pop()
        return ObjectMap({
            "compname": "regions/%s/snapshots/%s" % (
                region, component),
            "modname": "Snapshot status",
            "status": snapshot.status
        })


class EC2ImageStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS Image state.
    """

    def results_to_maps(self, region, component):
        image = self.ec2regionconn.get_all_images(component).pop()
        return ObjectMap({
            "compname": "regions/%s/images/%s" % (
                region, component),
            "modname": "Image state",
            "state": image.state
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


class EC2VolumeStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS Volumes status.
    """

    def results_to_maps(self, region, component):
        volume = self.ec2regionconn.get_all_volumes(component).pop()
        return ObjectMap({
            "compname": "regions/%s/volumes/%s" % (
                region, component),
            "modname": "Volume status",
            "status": volume.status
        })


class EC2UnreservedInstancesPlugin(AWSBasePlugin):
    def collect(self, config):
        def inner():
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
                    event = 'There is {0} instances of this type in this ' \
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
        return defer.maybeDeferred(inner)


class EC2UnusedReservedInstancesPlugin(AWSBasePlugin):
    def collect(self, config):
        def inner():
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
                    event = 'There is {0} reserved instances of this type ' \
                        'in this availability zone which are unused'.format(c)

                if event:
                    data['events'].append({
                        'summary': event,
                        'device': config.id,
                        'component': ds.component,
                        'severity': ZenEventClasses.Info,
                        'eventClass': '/AWS/Suggestion',
                    })
            return data
        return defer.maybeDeferred(inner)
