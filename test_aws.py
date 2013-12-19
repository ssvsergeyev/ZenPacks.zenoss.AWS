from pprint import pprint

from butils.config_parser import config_to_dict
credentials = config_to_dict('/home/zenoss/.boto')['credentials']

import boto
from boto.ec2.connection import EC2Connection
import boto.ec2.elb
import boto.sqs
import boto.s3

print '-' * 100

ec2conn = EC2Connection(**credentials)

aws_scheme = {}

for region in ec2conn.get_all_regions():

    region_scheme = {}

    s3_conn = boto.s3.connect_to_region(region.name, **credentials)
    print s3_conn.get_all_buckets()

    continue

    elb_conn = boto.ec2.elb.connect_to_region(region.name, **credentials)
    elbs = elb_conn.get_all_load_balancers()
    for elb in elbs:
        balancer_scheme = vars(elb)

        balancer_scheme['instances'] = [
            vars(instance)
            for instance in elb.instances
        ]

        region_scheme[elb.name] = balancer_scheme

    ec2_r_conn = boto.ec2.connect_to_region(region.name, **credentials)

    for reservation in ec2_r_conn.get_all_instances():
        reservation_scheme = vars(reservation)
        reservation_scheme['instances'] = dict(
            (instance.id, vars(instance))
            for instance in reservation.instances
        )
        region_scheme[reservation.id] = reservation_scheme

    
    sqsconnection = boto.sqs.connect_to_region(region.name, **credentials)    
    for queue in sqsconnection.get_all_queues():
        q_scheme = vars(queue)
        q_scheme['messages'] = map(vars, queue.get_messages())
        region_scheme[queue.id] = q_scheme

    aws_scheme[region.name] = region_scheme

print '-' * 100

pprint(aws_scheme)
