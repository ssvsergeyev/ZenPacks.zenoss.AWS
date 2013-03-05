###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013 Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

import logging
LOG = logging.getLogger('zen.AWS')

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps\
    import MultiArgs, ObjectMap, RelationshipMap

from ZenPacks.zenoss.AWS.utils \
    import addLocalLibPath, result_errmsg

addLocalLibPath()

from boto.ec2.connection import EC2Connection as ec2
from boto.vpc import VPCConnection as vpc


class EC2(PythonPlugin):

    ec2Queries = {
        }

    deviceProperties = PythonPlugin.deviceProperties + (
        'ec2accesskey', 'ec2secretkey')

    def collect(self, device, log):

        #Retrieve access key properties from Device
        accesskey = getattr(device, 'ec2accesskey', None)
        secretkey = getattr(device, 'ec2secretkey', None)

        ec2conn = ec2(accesskey, secretkey)

        # Get Region objects
        regions = ec2conn.get_all_regions()

        # List of instance states to collect
        ec2States = [
            'pending',
            'running',
            'shutting-down',
            'stopping',
            'stopped'
            ]

        filters = {'instance-state-name': ec2States}
        reservations = []
        vpcs = []
        zones = []
        volumes = []

        # Retrieve objects from all regions
        for region in regions:
            ec2regionconn = ec2(accesskey, secretkey, region=region)
            vpcregionconn = vpc(accesskey, secretkey, region=region)

            # Pull VPC Information
            vpcs.extend(
                    vpcregionconn.get_all_vpcs()
                )

            zones.extend(
                    ec2regionconn.get_all_zones()
                    )

            volumes.extend(
                    ec2regionconn.get_all_volumes()
                    )

            # Pull Instance Information
            reservations.extend(
                            ec2regionconn.get_all_instances(
                            filters=filters)
                        )
        # Pull all instance object from reservations into dictionary list
        instanceList = {}
        for reservation in reservations:
            for instance in reservation.instances:
                instanceList[instance] = instance

        d = {}
        d['instances'] = instanceList
        d['regions'] = regions
        d['zones'] = zones
        d['vpcs'] = vpcs
        d['volumes'] = volumes

        #import pdb; pdb.set_trace()
        return d

    def process(self, device, results, log):

        log.info('Modeler %s processing data for device %s',
            self.name(), device.id)

        ec2_manager_om = ObjectMap()
        maps = []

        # ObjectMap lists
        instance_oms = []
        vpc_oms = []
        zone_oms = []
        volume_oms = []

        for instance in results['instances']:
            instance_oms.append(self.get_instance_om(instance))

        for vpc in results['vpcs']:
            vpc_oms.append(self.get_vpc_om(vpc))

        for zone in results['zones']:
            zone_oms.append(self.get_zone_om(zone))

        for volume in results['volumes']:
            volume_oms.append(self.get_volume_om(volume))

        maps.extend([ec2_manager_om])

        maps.append(RelationshipMap(
            relname="instances",
            modname="ZenPacks.zenoss.AWS.EC2Instance",
            objmaps=instance_oms))

        maps.append(RelationshipMap(
            relname="vpcs",
            modname="ZenPacks.zenoss.AWS.EC2VPC",
            objmaps=vpc_oms))

        maps.append(RelationshipMap(
            relname="zones",
            modname="ZenPacks.zenoss.AWS.EC2Zone",
            objmaps=zone_oms))

        maps.append(RelationshipMap(
            relname="volumes",
            modname="ZenPacks.zenoss.AWS.EC2Volume",
            objmaps=volume_oms))

        #import pdb; pdb.set_trace()
        return maps

    def get_instance_om(self, instance):

        om = ObjectMap()
        om.id = self.prepId(instance.id)
        om.instance_id = instance.id
        om.title = instance.tags['Name']
        om.public_dns_name = instance.public_dns_name
        om.private_ip_address = instance.private_ip_address
        om.image_id = instance.image_id
        om.instance_type = instance.instance_type
        om.launch_time = instance.launch_time
        om.state = instance.state
        om.region = instance.region.name
        om.platform = getattr(instance, 'platform', '')
        om.vpc_id = instance.vpc_id
        #om.monitored = instance.monitored

        return om

    def get_vpc_om(self, vpc):
        om = ObjectMap()
        om.id = self.prepId(vpc.id)
        try:
            om.title = vpc.tags['Name']
        except:
            om.title = vpc.id
        om.cidr_block = vpc.cidr_block
        om.state = vpc.state
        om.region = vpc.region.name
        try:
            om.collector = self.prepId(vpc.tags['Collector'])
        except:
            om.collector = 'localhost'

        return om

    def get_zone_om(self, zone):
        om = ObjectMap()
        om.id = self.prepId(zone.name)
        try:
            om.title = zone.tags['Name']
        except:
            om.title = zone.name
        om.region = zone.region.name
        om.state = zone.state

        return om

    def get_volume_om(self, volume):
        om = ObjectMap()
        om.id = self.prepId(volume.id)
        om.zone = volume.zone
        om.create_time = volume.create_time
        om.region = volume.region.name
        om.size = str(volume.size)
        om.state = volume.status

        return om
