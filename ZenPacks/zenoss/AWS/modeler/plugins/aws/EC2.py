##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin

from Products.DataCollector.plugins.DataMaps\
    import MultiArgs, ObjectMap, RelationshipMap

from ZenPacks.zenoss.AWS.utils import addLocalLibPath, result_errmsg

addLocalLibPath()

from boto.ec2.connection import EC2Connection as ec2
from boto.vpc import VPCConnection as vpc

import pdb


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

        # Retrieve objects from all regions
        for region in regions:
            ec2regionconn = ec2(accesskey, secretkey, region=region)
            vpcretionconn = vpc(accesskey, secretkey, region=region)

            # Pull VPC Information
            vpcs.extend(
                    vpcretionconn.get_all_vpcs()
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
        d['vpcs'] = vpcs

        return d

    def process(self, device, results, log):

        log.info('Modeler %s processing data for device %s',
            self.name(), device.id)

        ec2_manager_om = ObjectMap()
        maps = []

        # ObjectMap lists
        instance_oms = []

        for instance in results['instances']:
            instance_oms.append(self.get_instance_om(instance))

        #ec2_manager_om.linuxDeviceClass = '/Server/SSH/Linux'

        maps.extend([ec2_manager_om])

        maps.append(RelationshipMap(
            relname="instances",
            modname="ZenPacks.zenoss.AWS.EC2Instance",
            objmaps=instance_oms))

        return maps

    def get_instance_om(self, instance):
        om = ObjectMap()
        om.id = self.prepId(instance.id)
        om.title = instance.tags['Name']
        om.public_dns_name = instance.public_dns_name
        om.private_ip_address = instance.private_ip_address
        om.image_id = instance.image_id
        om.instance_type = instance.instance_type
        om.launch_time = instance.launch_time
        om.state = instance.state
        om.region = instance.region.name
        om.platform = getattr(instance, 'platform', '')

        return om
