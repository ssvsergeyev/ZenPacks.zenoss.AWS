##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import collections
import json
from itertools import chain

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap

from Products.ZenUtils.Utils import prepId

from ZenPacks.zenoss.AWS import MODULE_NAME
from ZenPacks.zenoss.AWS.utils import addLocalLibPath

addLocalLibPath()

from boto.ec2.connection import EC2Connection
from boto.vpc import VPCConnection
from boto.s3.connection import S3Connection
import boto.sqs

'''
Models regions, instance types, zones, instances, volumes, VPCs and VPC
subnets for an Amazon EC2 account.
'''

class EC2(PythonPlugin):
    deviceProperties = PythonPlugin.deviceProperties + (
        'ec2accesskey',
        'ec2secretkey',
        'zAWSDiscover',
        'zAWSRegionPEM'
    )

    def collect(self, device, log):
        return True

    def process(self, device, results, log):
        log.info(
            'Modeler %s processing data for device %s',
            self.name(), device.id)

        accesskey = getattr(device, 'ec2accesskey', None)
        if not accesskey:
            log.error('%s: EC2 access key not set. Not discovering.')
            return

        secretkey = getattr(device, 'ec2secretkey', None)
        if not secretkey:
            log.error('%s: EC2 secret key not set. Not discovering.')
            return

        maps = collections.OrderedDict([
            ('regions', []),
            ('s3buckets', []),
            ('instance types', []),
            ('zones', []),
            ('VPCs', []),
            ('VPC subnets', []),
            ('VPNGateways', []),
            ('images', []),
            ('instances', []),
            ('volumes', []),
            ('snapshots', []),
            ('queues', []),
            ('elastic_ips', []),
            ('reservations', []),
            ('account', []),
        ])

        instance_filters = {
            'instance-state-name': [
                'pending',
                'running',
                'shutting-down',
                'stopping',
                'stopped',
            ],
        }

        image_filters = []

        ec2conn = EC2Connection(accesskey, secretkey)
        s3connection = S3Connection(accesskey, secretkey)

        region_oms = []
        for region in ec2conn.get_all_regions():
            region_id = prepId(region.name)

            region_oms.append(ObjectMap(data={
                'id': region_id,
                'title': region.name,
            }))

            ec2regionconn = EC2Connection(accesskey, secretkey, region=region)
            vpcregionconn = VPCConnection(accesskey, secretkey, region=region)
            sqsconnection = boto.sqs.connect_to_region(
                region.name,
                aws_access_key_id=accesskey,
                aws_secret_access_key=secretkey
            )
            # Zones
            maps['zones'].append(
                zones_rm(
                    region_id, ec2regionconn.get_all_zones())
            )

            # VPCs
            maps['VPCs'].append(
                vpcs_rm(
                    region_id, vpcregionconn.get_all_vpcs())
            )

            # VPNGateways
            maps['VPNGateways'].append(
                vpn_gateways_rm(
                    region_id, vpcregionconn.get_all_vpn_gateways())
            )

            maps['queues'].append(
                vpn_queues_rm(
                    region_id, sqsconnection.get_all_queues())
            )

            # VPC Subnets
            maps['VPC subnets'].append(
                vpc_subnets_rm(
                    region_id, vpcregionconn.get_all_subnets())
            )

            # Instances
            maps['instances'].append(
                instances_rm(
                    region_id,
                    device,
                    ec2regionconn.get_all_instances(filters=instance_filters),
                    image_filters
                )
            )

            # Images
            if image_filters:
                maps['images'].append(
                    images_rm(region_id, ec2regionconn.get_all_images(
                        image_ids=image_filters))
                )
                image_filters = []

            # Volumes
            maps['volumes'].append(
                volumes_rm(
                    region_id, ec2regionconn.get_all_volumes())
            )

            # Volumes
            maps['snapshots'].append(
                snapshots_rm(
                    region_id, ec2regionconn.get_all_snapshots(
                        owner="self"
                    ))
            )

            # Elastic IPs
            maps['elastic_ips'].append(
                elastic_ips_rm(
                    region_id, ec2regionconn.get_all_addresses())
            )

            # Reservations
            maps['reservations'].append(
                reservations_rm(
                    region_id, ec2regionconn.get_all_reserved_instances())
            )
            

        # Regions
        maps['regions'].append(RelationshipMap(
            relname='regions',
            modname=MODULE_NAME['EC2Region'],
            objmaps=region_oms))

        # S3Buckets
        maps['s3buckets'].append(
            s3buckets_rm(s3connection.get_all_buckets())
        )

        # Trigger discovery of instance guest devices.
        maps['account'].append(ObjectMap(data={
            'setDiscoverGuests': True,
        }))

        return list(chain.from_iterable(maps.itervalues()))


def name_or(tags, default):
    '''
    Return value of Name tag if it exists, or default otherwise.
    '''
    if 'Name' in tags:
        return tags['Name']

    return default


def tags_string(tegs):
    '''
    Return a string with clean tags.
    '''
    res = ''
    for teg in tegs:
        res = res + "{0}: {1}, ".format(teg, tegs[teg])
    return res[:-2] + ';'


def check_tag(values, tags):
    '''
    Return parsed zproperty.
    '''
    if values.strip():
        value = dict((k.strip(), v.strip()) for k, v in (x.split(':')
                     for x in values.split(';') if x.strip()))
    else:
        return False
    check = False
    for key in tags:
        try:
            if value[key] == tags[key]:
                check += True
        except:
            continue
    return True if check > 0 else False


def path_to_pem(region_name, values):
    '''
    Return path to PEM file of the region.
    '''
    if not values:
        return ''
    results = {}
    for value in values:
        result = json.loads(value)
        results.update({result['region_name']: result['pem_path']})

    if not region_name in results:
        return ''
    return results[region_name]


def to_boolean(string):
    '''
    Return a boolean given a string representation of a boolean.
    '''
    return {
        'true': True,
        'false': False,
    }.get(string.lower())


def zones_rm(region_id, zones):
    '''
    Return zones RelationshipMap given region_id and ZoneInfo ResultSet.
    '''
    zone_data = []
    for zone in zones:
        zone_data.append({
            'id': prepId(zone.name),
            'title': zone.name,
            'state': zone.state,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='zones',
        modname=MODULE_NAME['EC2Zone'],
        objmaps=zone_data)


def vpcs_rm(region_id, vpcs):
    '''
    Return vpcs RelationshipMap given region_id and VPCInfo ResultSet.
    '''
    vpc_data = []
    for vpc in vpcs:
        if 'Collector' in vpc.tags:
            collector = prepId(vpc.tags['Collector'])
        else:
            collector = None

        vpc_data.append({
            'id': prepId(vpc.id),
            'title': name_or(vpc.tags, vpc.id),
            'cidr_block': vpc.cidr_block,
            'state': vpc.state,
            'collector': collector,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='vpcs',
        modname=MODULE_NAME['EC2VPC'],
        objmaps=vpc_data)


def vpn_gateways_rm(region_id, gateways):
    '''
    Return VPN Gateways RelationshipMap
    given region_id and list of VpnGateway objects
    '''
    objmaps = []
    for gateway in gateways:
        objmaps.append({
            'id': prepId(gateway.id),
            'title': name_or(gateway.tags, gateway.id),
            'state': gateway.state,
            'availability_zone': gateway.availability_zone,
            'gateway_type': gateway.type,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='vpn_gateways',
        modname=MODULE_NAME['VPNGateway'],
        objmaps=objmaps
    )


def vpn_queues_rm(region_id, qs):
    objmaps = []
    for q in qs:
        objmaps.append({
            'id': prepId(q.id),
            'title': q.name,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='queues',
        modname=MODULE_NAME['SQSQueue'],
        objmaps=objmaps
    )


def vpc_subnets_rm(region_id, subnets):
    '''
    Return vpc_subnets RelationshipMap given region_id and a SubnetInfo
    ResultSet.
    '''
    vpc_subnet_data = []
    for subnet in subnets:
        vpc_subnet_data.append({
            'id': prepId(subnet.id),
            'title': name_or(subnet.tags, subnet.id),
            'available_ip_address_count': subnet.available_ip_address_count,
            'cidr_block': subnet.cidr_block,
            'defaultForAz': to_boolean(subnet.defaultForAz),
            'mapPublicIpOnLaunch': to_boolean(subnet.mapPublicIpOnLaunch),
            'state': subnet.state,
            'setVPCId': subnet.vpc_id,
            'setZoneId': subnet.availability_zone,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='vpc_subnets',
        modname=MODULE_NAME['EC2VPCSubnet'],
        objmaps=vpc_subnet_data)


def instances_rm(region_id, device, reservations, image_filters):
    '''
    Return instances RelationshipMap given region_id and an InstanceInfo
    ResultSet.
    '''
    instance_data = []
    for instance in chain.from_iterable(r.instances for r in reservations):
        zone_id = prepId(instance.placement) if instance.placement else None
        subnet_id = prepId(instance.subnet_id) if instance.subnet_id else None

        image_filters.append(instance.image_id)

        instance_data.append({
            'id': prepId(instance.id),
            'title': name_or(instance.tags, instance.id),
            'instance_id': instance.id,
            'tags': tags_string(instance.tags),
            'public_dns_name': instance.public_dns_name,
            'public_ip': instance.ip_address,
            'private_ip_address': instance.private_ip_address,
            'instance_type': instance.instance_type,
            'launch_time': instance.launch_time,
            'state': instance.state,
            'platform': getattr(instance, 'platform', ''),
            'detailed_monitoring': instance.monitored,
            'setZoneId': zone_id,
            'setImageId': instance.image_id,
            'setVPCSubnetId': subnet_id,
            'guest': check_tag(device.zAWSDiscover, instance.tags),
            'pem_path': path_to_pem(region_id, device.zAWSRegionPEM),
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='instances',
        modname=MODULE_NAME['EC2Instance'],
        objmaps=instance_data)


def images_rm(region_id, images):
    '''
    Return images RelationshipMap given region_id and an ImageInfo
    ResultSet.
    '''
    image_data = []
    for image in images:
        image_data.append({
            'id': prepId(image.id),
            'title': image.name,
            'location': image.location,
            'state': image.state,
            'owner_id': image.owner_id,
            'architecture': image.architecture,
            'platform': image.platform,
            'image_type': image.type,
            'kernel_id': image.kernel_id,
            'ramdisk_id': image.ramdisk_id,
            'description': image.description,
            'block_device_mapping': str(image.block_device_mapping),
            'root_device_type': image.root_device_type,
            'root_device_name': image.root_device_name,
            'virtualization_type': image.virtualization_type,
            'hypervisor': image.hypervisor,
            })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='images',
        modname=MODULE_NAME['EC2Image'],
        objmaps=image_data
    )


def volumes_rm(region_id, volumes):
    '''
    Return volumes RelationshipMap given region_id and a VolumeInfo
    ResultSet.
    '''
    volume_data = []
    for volume in volumes:
        if volume.attach_data.instance_id:
            instance_id = prepId(volume.attach_data.instance_id)
        else:
            instance_id = None

        volume_data.append({
            'id': prepId(volume.id),
            'title': name_or(volume.tags, volume.id),
            'volume_type': volume.type,
            'create_time': volume.create_time,
            'size': volume.size / (1024 ** 3),
            'iops': volume.iops,
            'status': volume.status,
            'attach_data_status': volume.attach_data.status,
            'attach_data_devicepath': volume.attach_data.device,
            'setInstanceId': instance_id,
            'setZoneId': volume.zone,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='volumes',
        modname=MODULE_NAME['EC2Volume'],
        objmaps=volume_data)


def snapshots_rm(region_id, snapshots):
    '''
    Return snapshots RelationshipMap given region_id and a Snapshot
    ResultSet.
    '''
    snapshot_data = []
    for snapshot in snapshots:
        if snapshot.volume_id:
            volume_id = prepId(snapshot.volume_id)
        else:
            volume_id = None

        snapshot_data.append({
            'id': prepId(snapshot.id),
            'title': name_or(snapshot.tags, snapshot.id),
            'description': snapshot.description,
            'size': snapshot.volume_size / (1024 ** 3),
            'status': snapshot.status,
            'progress': snapshot.progress,
            'start_time': snapshot.start_time,
            'setVolumeId': volume_id,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='snapshots',
        modname=MODULE_NAME['EC2Snapshot'],
        objmaps=snapshot_data)


def elastic_ips_rm(region_id, elastic_ips):
    '''
    Return Elastic IPs RelationshipMap given region_id and an Elastic IP Info
    ResultSet.
    '''
    elastic_ip_data = []
    for elastic_ip in elastic_ips:
        elastic_ip_data.append({
            'id': prepId(elastic_ip.public_ip),
            'title': elastic_ip.public_ip,
            'public_ip': elastic_ip.public_ip,
            'private_ip_address': elastic_ip.private_ip_address,
            'instance_id': elastic_ip.instance_id,
            'domain': elastic_ip.domain,
            'network_interface_id': elastic_ip.network_interface_id,
            'network_interface_owner_id':
            elastic_ip.network_interface_owner_id,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='elastic_ips',
        modname=MODULE_NAME['EC2ElasticIP'],
        objmaps=elastic_ip_data)


def reservations_rm(region_id, reservations):
    '''
    Return Reservations RelationshipMap given region_id and an ReservationInfo
    ResultSet.
    '''
    reservation_data = []
    for reservation in reservations:
        reservation_data.append({
            'id': prepId(reservation.id),
            'title': reservation.id,
            'instance_type': reservation.instance_type,
            'availability_zone': reservation.availability_zone,
            'duration': reservation.duration,
            'description': reservation.description,
            'instance_tenancy': reservation.instance_tenancy,
            'offering_type': reservation.offering_type,
            'state': reservation.state,
        })

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='reservations',
        modname=MODULE_NAME['EC2Reservation'],
        objmaps=reservation_data)


def s3buckets_rm(buckets):
    '''
    Return buckets RelationshipMap given a BucketInfo
    ResultSet.
    '''
    bucket_oms = []
    for bucket in buckets:
        bucket_oms.append(ObjectMap(data={
            'id': prepId(bucket.name),
            'title': bucket.name,
            'creation_date': bucket.creation_date,
        }))

    return RelationshipMap(
        relname='s3buckets',
        modname=MODULE_NAME['S3Bucket'],
        objmaps=bucket_oms)
