from pprint import pprint
import sys

import boto
from boto.ec2.connection import EC2Connection
import boto.ec2.elb
import boto.sqs
from boto.sqs.message import RawMessage
import boto.s3

print '-' * 100
yuriy = dict(
    aws_access_key_id='AKIAJZS27O6JHGMRC5RA',
    aws_secret_access_key='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',
)
taras = dict(
    aws_access_key_id='AKIAIFFAHXR3ZADGOOAA',
    aws_secret_access_key='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',
)
credentials = taras
ec2conn = EC2Connection(**credentials)

aws_scheme = {}

def get_instances(ec2):
    return map(vars, ec2.get_only_instances())

def clear_paid_services():
    for region in ec2conn.get_all_regions():
        ec2_r_conn = boto.ec2.connect_to_region(region.name, **credentials)
        instance_ids = [i.id for i in ec2_r_conn.get_only_instances()]
        if instance_ids:
            print 'Terminating', ', '.join(instance_ids)
            ec2_r_conn.terminate_instances(instance_ids=instance_ids)
        for address in ec2_r_conn.get_all_addresses():
            print address.public_ip,
            if not address.association_id:
                print 'not associated, releasing'
                address.release()
            else:
                print 'is associated with', address.association_id

def get_messages(queue):
    messages = {}
    message_count = -1
    while message_count < len(messages):
        message_count = len(messages)
        res = queue.get_messages(num_messages=10, visibility_timeout=3)
        for message in res:
            messages[message.id] = message._body
    return messages

def get_queues(region_name):
    sqs = boto.sqs.connect_to_region(region_name, **credentials)
    res = []
    for queue in sqs.get_all_queues():
        queue.set_message_class(RawMessage)
        q_scheme = {}
        # q_scheme = vars(queue)
        q_scheme['messages'] = get_messages(queue)
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


def show_scheme():
    for region in ec2conn.get_all_regions():

        region_scheme = {}

        ec2_r_conn = boto.ec2.connect_to_region(region.name, **credentials)
        region_scheme['instances'] = get_instances(ec2_r_conn)
        # region_scheme['queues'] = get_queues(region.name)
        # region_scheme['balancers'] = get_balancers(region.name)
        # region_scheme['buckets'] = get_buckets(region.name)

        aws_scheme[region.name] = region_scheme

    print '-' * 100

    pprint(aws_scheme)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'clear_paid':
        clear_paid_services()
    else:
        show_scheme()
