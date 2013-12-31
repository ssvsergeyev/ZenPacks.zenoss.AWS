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

def get_instances(ec2):
    return map(vars, ec2.get_only_instances())

def get_queues(region_name):
    sqs = boto.sqs.connect_to_region(region_name, **credentials)
    res = []
    for queue in sqs.get_all_queues():
        q_scheme = vars(queue)
        # q_scheme['messages'] = map(vars, queue.get_messages())
        q_scheme['id'] = queue.id
        q_scheme['name'] = queue.name
        res.append(q_scheme)
    return res

def get_balancers(region_name):
    res = []
    elb_conn = boto.ec2.elb.connect_to_region(region_name, **credentials)
    for elb in elb_conn.get_all_load_balancers():
        balancer_scheme = vars(elb)

        balancer_scheme['instances'] = [
            vars(instance)
            for instance in elb.instances
        ]
        res.append(balancer_scheme)
    return res

def get_buckets(region_name):
    s3_conn = boto.s3.connect_to_region(region.name, **credentials)
    return map(vars, s3_conn.get_all_buckets())

for region in ec2conn.get_all_regions():

    region_scheme = {}

    ec2_r_conn = boto.ec2.connect_to_region(region.name, **credentials)
    # region_scheme['instances'] = get_instances(ec2_r_conn)
    region_scheme['queues'] = get_queues(region.name)
    # region_scheme['balancers'] = get_balancers(region.name)
    # region_scheme['buckets'] = get_buckets(region.name)

    aws_scheme[region.name] = region_scheme

print '-' * 100

pprint(aws_scheme)
