##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

'''
Collects information about AWS EC2 infrastructure.
'''

import collections
import json

from itertools import chain
from logging import getLogger
log = getLogger('zen.ZenModeler')

from socket import gaierror

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap

from Products.ZenUtils.Utils import prepId

from ZenPacks.zenoss.AWS import MODULE_NAME
from ZenPacks.zenoss.AWS.utils import addLocalLibPath, prodState, format_time

addLocalLibPath()

from boto.ec2.connection import EC2Connection, EC2ResponseError
from boto.vpc import VPCConnection
import boto.sqs

'''
Models regions, instance types, zones, instances, volumes, VPCs and VPC
subnets for an Amazon EC2 account.
'''
INSTANCE_FILTERS = {
    'instance-state-name': [
        'pending',
        'running',
        'shutting-down',
        'stopping',
        'stopped',
    ],
}


class EC2(PythonPlugin):
    deviceProperties = PythonPlugin.deviceProperties + (
        'ec2accesskey',
        'ec2secretkey',
        'zAWSDiscover',
        'zAWSRegionPEM',
        'zAWSRegionToModel',
    )

    def collect(self, device, log):
        return True

    def process(self, device, results, log):
        log.info(
            'Modeler %s processing data for device %s',
            self.name(), device.id)

        accesskey = getattr(device, 'ec2accesskey', None)
        secretkey = getattr(device, 'ec2secretkey', None)

        old_logger = boto.log.error
        boto.log.error = lambda x: x
        try:
            if not secretkey or not accesskey:
                raise EC2ResponseError('', '', '')
            ec2conn = EC2Connection(accesskey, secretkey)
            ec2_regions = ec2conn.get_all_regions()
        except EC2ResponseError:
            log.error('Invalid Keys. '
                      'Check your EC2 Access Key and EC2 Secret Key.')
            return
        except gaierror, e:
            log.error(e.strerror)
            return
        finally:
            boto.log.error = old_logger

        maps = collections.OrderedDict([
            ('regions', []),
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
            ('reserved_instances', []),
        ])

        images = []

        region_oms = []
        instance_states = {}
        for region in ec2_regions:
            # Controls which region(s) to model
            if device.zAWSRegionToModel:
                if not region.name in device.zAWSRegionToModel:
                    continue

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
                    region_id, vpcregionconn.get_all_vpn_gateways()
                )
            )

            maps['queues'].append(vpn_queues_rm(
                region_id, sqsconnection.get_all_queues()
            ))

            maps['VPC subnets'].append(vpc_subnets_rm(
                region_id, vpcregionconn.get_all_subnets()
            ))

            # Instances
            maps['instances'].append(instances_rm(
                region_id,
                device,
                ec2regionconn.get_only_instances(filters=INSTANCE_FILTERS),
                images,
                instance_states,
                ec2regionconn
            ))

            # Images
            if images:
                maps['images'].append(
                    images_rm(region_id, images
                ))
                images = []
            region_volumes = ec2regionconn.get_all_volumes()
            region_volume_ids = {x.id:1 for x in region_volumes}

            maps['volumes'].append(volumes_rm(
                region_id, region_volumes
            ))

            maps['snapshots'].append(snapshots_rm(
                region_id, ec2regionconn.get_all_snapshots(
                    owner="self"
                ), region_volume_ids
            ))

            # Elastic IPs
            maps['elastic_ips'].append(
                elastic_ips_rm(
                    region_id, ec2regionconn.get_all_addresses())
            )

            maps['reserved_instances'].append(
                reserved_instances_rm(
                    region_id,
                    ec2regionconn.get_all_reserved_instances(),
                    instance_states
                )
            )

        # Regions
        maps['regions'].append(RelationshipMap(
            relname='regions',
            modname=MODULE_NAME['EC2Region'],
            objmaps=region_oms))

        # Trigger discovery of instance guest devices.
        maps['account'].append(ObjectMap(data={
            'setDiscoverGuests': sorted(instance_states.items())
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
    if res:
        return res[:-2] + ';'


def check_tag(values, tags):
    '''
    Return parsed zproperty.

    @param values: zAWSDiscover values
    @type values: str
    @param tags: instance's tags
    @type tags: dict
    '''
    if values.strip():
        try:
            value = set((k.strip(), v.strip()) for k, v in (x.split(':')
                        for x in values.split(';') if x.strip()))
        except:
            return False
    else:
        # return True if zAWSDiscover is not set.
        return True
    check = False
    for key in tags:
        try:
            for k, v in value:
                if k == key.strip() and v == tags[key].strip():
                    check += True
        except:
            continue
    return True if check > 0 else False


def block_device(devices):
    """
    Return comma separated list of volumes associated with AMI.
    Indicates if it's the root device, provides device name,
    the snapshot ID, capacity of volume in GiB when launched,
    and whether that volume should be deleted on instance termination.
    """
    if not devices:
        return ''

    block_device_properties = (
        'ephemeral_name',
        'snapshot_id',
        'size',
        'delete_on_termination',
        'volume_type'
    )
    result = []
    for dev in devices:
        res = '%s%s' % (dev, '=')
        for prop in block_device_properties:
            if getattr(devices[dev], prop):
                res += '%s%s' % (getattr(devices[dev], prop), ':')
        result.append(res[:-1])
    return ', '.join(result)


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


def format_size(size):
    '''
    Return formatted  capacity value for volumes and snapshots.
    The capacity for these components is between 1 GiB and 1 TiB.
    '''
    if size:
        return '{0} GB'.format(size) if size < 1024 \
            else '{0} TB'.format(size/1024)


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
            'id': prepId('queue_' + q.name),
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


def get_instance_data(instance, image_ids):
    zone_id = prepId(instance.placement) if instance.placement else None
    subnet_id = prepId(instance.subnet_id) if instance.subnet_id else None

    if instance.image_id in image_ids:
        instance_image_id = instance.image_id
    else:
        instance_image_id = None

    return {
        'id': prepId(instance.id),
        'title': name_or(instance.tags, instance.id),
        'instance_id': instance.id,
        'tags': tags_string(instance.tags),
        'public_dns_name': instance.public_dns_name,
        'public_ip': instance.ip_address,
        'private_ip_address': instance.private_ip_address,
        'instance_type': instance.instance_type,
        'launch_time': format_time(instance.launch_time),
        'state': instance.state,
        'platform': getattr(instance, 'platform', ''),
        'detailed_monitoring': instance.monitored,
        'setZoneId': zone_id,
        'setImageId': instance_image_id,
        'setVPCSubnetId': subnet_id,
    }


def instances_rm(region_id, device, instances, images, instance_states, region_conn):
    '''
    Return instances RelationshipMap given region_id and an InstanceInfo
    ResultSet.
    '''
    instance_data = []
    image_filters = []
    for instance in instances:
        image_filters.append(instance.image_id)

    if image_filters:
        data = region_conn.get_all_images(image_ids=image_filters)
        images.extend(data)

    image_ids = [x.id for x in images]
    for instance in instances:
        data = get_instance_data(instance, image_ids)
        data.update({
            'guest': check_tag(device.zAWSDiscover, instance.tags),
            'pem_path': path_to_pem(region_id, device.zAWSRegionPEM),
        })
        instance_states[data['id']] = prodState(data['state'])
        instance_data.append(data)

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='instances',
        modname=MODULE_NAME['EC2Instance'],
        objmaps=instance_data
    )

def images_rm(region_id, images):
    '''
    Return images RelationshipMap given region_id and an ImageInfo
    ResultSet.
    '''
    image_data = []
    for image in images:
        image_data.append({
            'id': prepId(image.id),
            'title': image.name if image.name else image.id,
            'location': image.location,
            'state': image.state,
            'owner_id': image.owner_id,
            'architecture': image.architecture,
            # 'platform': getattr(image, 'platform', ''),
            'image_type': image.type,
            'kernel_id': image.kernel_id,
            'ramdisk_id': image.ramdisk_id,
            'description': image.description,
            'block_device_mapping': block_device(image.block_device_mapping),
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
            'create_time': format_time(volume.create_time),
            'size': format_size(volume.size),  # Min:1GiB, Max:1TiB
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


def snapshots_rm(region_id, snapshots, region_volume_ids):
    '''
    Return snapshots RelationshipMap given region_id and a Snapshot
    ResultSet.
    '''
    snapshot_data = []
    for snapshot in snapshots:
        if snapshot.volume_id:
            if snapshot.volume_id in region_volume_ids:
                volume_id = prepId(snapshot.volume_id)
            else:
                volume_id = None
        else:
            volume_id = None
        snapshot_data.append({
            'id': prepId(snapshot.id),
            'title': name_or(snapshot.tags, snapshot.id),
            'description': snapshot.description,
            'size': format_size(snapshot.volume_size),
            'status': snapshot.status,
            'progress': snapshot.progress,
            'start_time': format_time(snapshot.start_time),
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


def reserved_instances_rm(region_id, reserved_instances, instance_states):
    obj_map = []
    for ri in reserved_instances:
        # ZEN-17556: Ignore reserved instances with a None id.
        if ri.id is None:
            continue

        obj_map.append({
            'id': prepId(ri.id),
            'title': ri.id,
            'instance_type': ri.instance_type,
            'availability_zone': ri.availability_zone,
            'state': ri.state,
        })

        instance_states[prepId(ri.id)] = prodState(ri.state)

    return RelationshipMap(
        compname='regions/%s' % region_id,
        relname='reserved_instances',
        modname=MODULE_NAME['EC2ReservedInstance'],
        objmaps=obj_map
    )
