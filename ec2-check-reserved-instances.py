#!/usr/bin/python

import sys
import os
import boto
import boto.ec2
from pprint import pprint

from butils.config_parser import config_to_dict
creds = config_to_dict('/home/zenoss/.boto')['credentials']

def unreserved_instance_count(ec2_conn, instance):
    if instance.state != 'running':
        return 0 # stoppend instances not need discount
    if instance.spot_instance_request_id:
        return 0 # spot instances cannot use discount

    # getting running instances of the same type in the same availability zone and 
    instances = ec2_conn.get_only_instances(filters={
        'instance-state-name': 'running',
        'instance-type': instance.instance_type,
        'availability-zone': instance.placement,
    })
    # and not spot instances
    instances = filter(lambda i: not i.spot_instance_request_id, instances)

    # getting active reserved instances of the same type in the same availability zone and 
    reserved = ec2_conn.get_all_reserved_instances(filters={
        'state': 'active',
        'instance-type': instance.instance_type,
        'availability-zone': instance.placement,
    })
    return len(instances) - len(reserved_instances) 

running_instances = {}
reserved_instances = {}

ec2_conn = boto.ec2.connection.EC2Connection(**creds)

for region in ec2_conn.get_all_regions():
    print region.name
    ec2_conn = boto.ec2.connect_to_region(region.name, **creds)

    for instance in ec2_conn.get_only_instances():
        print instance
        if instance.state != "running":
            sys.stderr.write("Disqualifying instance %s: not running\n" % ( instance.id ) )
        elif instance.spot_instance_request_id:
            sys.stderr.write("Disqualifying instance %s: spot\n" % ( instance.id ) )
        else:
            if instance.vpc_id:
                print "Does not support vpc yet, please be careful when trusting these results"
            # else:
            if True:
                az = instance.placement
                instance_type = instance.instance_type
                unreserved = unreserved_instance_count(ec2_conn, instance)
                print instance.placement, instance.instance_type, unreserved
                # running_instances[ (instance_type, az ) ] = running_instances.get( (instance_type, az ) , 0 ) + 1

    # for reserved_instance in ec2_conn.get_all_reserved_instances():
    #     if reserved_instance.state != "active":
    #         sys.stderr.write( "Excluding reserved instances %s: no longer active\n" % ( reserved_instance.id ) )
    #     else:
    #         az = reserved_instance.availability_zone
    #         instance_type = reserved_instance.instance_type
    #         reserved_instances[( instance_type, az) ] = reserved_instances.get ( (instance_type, az ), 0 )  + reserved_instance.instance_count

# for each availability_zone and instance type, if in that zone-type there are more instances than reserved instances, than some instances could be reserved, else if there are more reserved instances than instances - some reserved instances are not used.

