#!/usr/bin/env python
##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


import sys
import os
import fcntl
import time
from datetime import datetime, timedelta
import pickle
import operator
import logging
import pdb
logging.basicConfig()
log = logging.getLogger('ec2')


libDir = os.path.join(os.path.dirname(__file__), '../lib')
if os.path.isdir(libDir):
    sys.path.append(libDir)

import boto
logging.getLogger('boto').setLevel(logging.CRITICAL)

ZENHOME = os.getenv('ZENHOME', '/opt/zenoss')
CACHE_LIFE = 600
CACHE_FILE = os.path.join(ZENHOME, 'var', '.ec2cache')
STATS_FILE = os.path.join(ZENHOME, 'var', '.ec2stats')

DP_NAMES = (
    'CPUUtilization',
    'NetworkIn',
    'NetworkOut',
    'DiskReadBytes',
    'DiskWriteBytes',
    'DiskReadOps',
    'DiskWriteOps'
)

def getOpts():
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("-r", "--range", dest="range",
        help="time range to poll in seconds ", default=300, type='int')

    parser.add_option("-v", "--logseverity", dest="logseverity",
        help="desired log level", default=0, type='int')

    parser.add_option("-c", "--consolidate",
        dest="consolidate", default='Average',
        help="Consolidation function (Average, Minimum, Maximum, Sum, Samples)")

    parser.add_option("--units", dest="units", default="",
        help="units in which data is returned ('Seconds', 'Percent', 'Bytes', "
         "'Bits', 'Count', 'Bytes/Second', 'Bits/Second', 'Count/Second')")

    parser.add_option("-u","--userkey", dest="userkey",
                      default=os.environ.get('AWS_ACCESS_KEY_ID', None))

    parser.add_option("-p","--privatekey", dest="privatekey",
                      default=os.environ.get('AWS_SECRET_ACCESS_KEY', None))
    parser.add_option("-i","--instance", dest="instance",default="")
    parser.add_option("--cachefile", dest="cachefile", default=CACHE_FILE)

    return parser.parse_args()


def work(opts):
    import time
    units = opts.units
    consolidate = opts.consolidate
    seconds = opts.range

    conn_kwargs = {
        'aws_access_key_id': opts.userkey,
        'aws_secret_access_key': opts.privatekey,
    }
    
    instances = [i for i in getCurrentInstances( conn_kwargs ) if i]
    
    conn = boto.connect_cloudwatch(**conn_kwargs)
    #metrics=reduce(lambda x,y:x+y,[conn.list_metrics(dimensions={'InstanceId':i}) for i in instances])

    end = datetime.utcnow()
    start = end - timedelta(seconds=seconds+5)
    
    for i in instances:
        id = 'InstanceId:' + i
        #nagios format
        output = id
        metrics = conn.list_metrics(dimensions={'InstanceId':i})
        if len(metrics) == 0:
            continue
        for m in metrics:
            ret = m.query(start, end, consolidate, units, seconds)
            if len(ret) > 0:
                output += " %s %0.2f" % (m.name,ret[-1][consolidate])
        print output
    
def getCurrentInstances( conn_kwargs ):
    '''
    Collect all the instances across all the
    systems (east, west, etc.). Leave out 
    terminated instances
    '''

    ec2conn = boto.connect_ec2(**conn_kwargs)
    ec2instances = []
    regions = ec2conn.get_all_regions()
    try:
        for region in regions:
            conn = region.connect(**conn_kwargs)
            for reservation in conn.get_all_instances():
                for instance in reservation.instances:
                    if instance.state == 'terminated': continue
                    ec2instances.append(instance.id)
    except boto.exception.EC2ResponseError, ex:
        print "ERROR:%s" % ex.error_message
        sys.exit(1)
    return ec2instances


def main():
    opts, myargs = getOpts()
    if not myargs:
        print "zencw2.py command [options] need to have command " \
              "EC2Manager, EC2Instance, EC2InstanceType or EC2ImageId"
        raise SystemExit(3)
    targetType = myargs[0][3:]
    if targetType not in ('Manager', 'Instance', 'InstanceType', 'ImageId'):
        print "zencw2.py command [options] command must be of type " \
              "EC2Manager, EC2Instance, EC2InstanceType or EC2ImageId"
        raise SystemExit(3)
    
    work(opts)
    exit()


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)
