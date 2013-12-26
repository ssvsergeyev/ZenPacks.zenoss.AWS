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

import boto
import boto.ec2
import boto.sqs
import boto.vpc

from boto.s3.connection import S3Connection
from twisted.internet import defer

from Products.DataCollector.plugins.DataMaps import ObjectMap
from Products.ZenEvents import ZenEventClasses
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin

from ZenPacks.zenoss.AWS.utils import unreserved_instance_count
from ZenPacks.zenoss.AWS.utils import unused_reserved_instances_count


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
        log.error(result)
        return {
            'vaues': {},
            'events': [{
                'summary': 'error: %s' % result,
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': ZenEventClasses.Error,
            }],
            'maps': [],
        }


class S3BucketPlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS S3Buckets.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
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
    Subclass of AWSBasePlugin to monitor AWS EC2Region soft limits.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
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
                ds.component,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )
            vpcregionconn = boto.vpc.connect_to_region(
                ds.component,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )

            instances_count = len(ec2regionconn.get_all_instances(
                filters=instance_filters
            ))
            elastic_ips_count = len(ec2regionconn.get_all_addresses())
            subnets_count = len(vpcregionconn.get_all_subnets())
            volumes_count = len(ec2regionconn.get_all_volumes())
            sg = yield ec2regionconn.get_all_security_groups()
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

        defer.returnValue(data)


class SQSQueuePlugin(AWSBasePlugin):
    """
    Subclass of AWSBasePlugin to monitor AWS SQSQueue.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
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
                        'eventClass': '/AWS/SQSMessage',
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
    Subclass of AWSBasePlugin to monitor AWS Zone.
    """

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
        for ds in config.datasources:
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

    @defer.inlineCallbacks
    def collect(self, config):
        data = self.new_data()
        for ds in config.datasources:
            region = yield ds.params['region']
            self.ec2regionconn = boto.ec2.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )

            self.vpcregionconn = boto.vpc.connect_to_region(
                region,
                aws_access_key_id=ds.ec2accesskey,
                aws_secret_access_key=ds.ec2secretkey,
            )

            data['maps'].append(
                self.results_to_maps(region, ds.component)
            )
        defer.returnValue(data)


class EC2InstanceStatePlugin(EC2BaseStatePlugin):
    """
    Subclass of EC2BaseStatePlugin to monitor AWS Instance state.
    """

    def results_to_maps(self, region, component):
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
                region = ds.params['region']
                ec2_conn = boto.ec2.connect_to_region(region,
                    aws_access_key_id=ds.ec2accesskey,
                    aws_secret_access_key=ds.ec2secretkey,
                )
                instance = ec2_conn.get_only_instances(ds.component).pop()
                c = unreserved_instance_count(ec2_conn, instance)

                event = None
                if c == 1:
                    event = 'This instance could be reserved'
                elif c > 1:
                    event = 'There is %s instances of this type in this availability zone which could be reserved' % c

                if event:
                    data['events'].append({
                        'summary': event,
                        'device': config.id,
                        'component': ds.component,
                        'severity': ZenEventClasses.Error,
                        'eventClass': '/AWS/Suggestion',
                    })
            return data
        return defer.maybeDeferred(inner)


class EC2UnusedReservedInstancesPlugin(AWSBasePlugin):
    def collect(self, config):
        def inner():
            data = self.new_data()
            for ds in config.datasources:
                region = ds.params['region']
                ec2_conn = boto.ec2.connect_to_region(region,
                    aws_access_key_id=ds.ec2accesskey,
                    aws_secret_access_key=ds.ec2secretkey,
                )
                try:
                    reserved_instance = ec2_conn.get_all_reserved_instances(ds.component).pop()
                except boto.exception.EC2ResponseError as e:
                    data['events'].append({
                        'summary': str(e),
                        'device': config.id,
                        'component': ds.component,
                        'severity': ZenEventClasses.Error,
                        'eventClass': '/Status',
                    })
                    return data
                c = unused_reserved_instances_count(ec2_conn, reserved_instance)

                event = None
                if c == 1:
                    event = 'This reserved instance is unused'
                elif c > 1:
                    event = 'There is %s reserved instances of this type in this availability zone which are unused' % c

                if event:
                    data['events'].append({
                        'summary': event,
                        'device': config.id,
                        'component': ds.component,
                        'severity': ZenEventClasses.Error,
                        'eventClass': '/AWS/Suggestion',
                    })
            return data
        return defer.maybeDeferred(inner)
