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


def work(opts,targetType):
    import time
    units = opts.units
    consolidate = opts.consolidate
    seconds = opts.range

    conn_kwargs = {
        'aws_access_key_id': opts.userkey,
        'aws_secret_access_key': opts.privatekey,
    }
    
    
    conn = boto.connect_cloudwatch(**conn_kwargs)
    #metrics=reduce(lambda x,y:x+y,[conn.list_metrics(dimensions={'InstanceId':i}) for i in instances])

    end = datetime.utcnow()
    start = end - timedelta(seconds=seconds+5)
    
    instTypes={}
    instances = getInstances(conn_kwargs)
    for i in instances:
        if not instTypes.has_key(i.instance_type):
            instTypes[i.instance_type]=None
    instTypes=instTypes.keys()
    
    if targetType == 'Instance':
        for i in instances:
            output = 'InstanceId:' + i.id
            metrics = conn.list_metrics(dimensions={'InstanceId':i.id})
            if len(metrics) == 0:
                continue
            for m in metrics:
                ret = m.query(start, end, consolidate, units, seconds)
                if len(ret) > 0:
                    output += " %s %0.2f" % (m.name,ret[-1][consolidate])
            print output
    elif targetType == 'InstanceType':
        for t in instTypes:
            output = 'InstanceType:' + t
            for m in conn.list_metrics(dimensions={'InstanceType':t}):
                ret = m.query(start, end, consolidate, units, seconds)
                output += " %s %0.2f" % (m.name,ret[-1][consolidate])
            print output

def getEBSVols():
    vols=ec2conn.get_all_volumes()
    vols=[v for v in vols if v.attachment_state() == 'attached']
    byInst = {}
    for v in vols:
        k=v.attach_data.instance_id
        byInst[k] = byInst.get(k,[]) + [v]
    return byInst

def query_with_backoff(metric,
                       start=datetime.utcnow() - timedelta(seconds=600),
                       end=datetime.utcnow(),
                       consolidate='Average',
                       units=None,
                       seconds=None):
    delay = 1
    tries = 4
    while(True):
        try:
            ret=m.query(start,end,consolidate,units,seconds)
            return ret
        except boto.exception.BotoServerError as ex:
            if ex.body.find('Throttling') > -1:
                print "throttled"
                tries -= 1
                delay *= 2
            else:
                raise ex
    return None

def aggEBSmetrics(volumes):
    readOps = 0
    writeOps = 0
    readBytes = 0.0
    writeBytes = 0.0
    end = datetime.utcnow()
    start = end - timedelta(seconds=600+5)
    for v in volumes:
        mets=[m for m in conn.list_metrics(dimensions={'VolumeId':v.id})
              if m.name in ['VolumeReadOps','VolumeWriteBytes','VolumeReadBytes','VolumeWriteOps']]
        for m in mets:
            ret=query_with_backoff(m,start,end,consolidate,units,seconds)
            if len(ret)>0:
                if m.name == 'VolumeReadOps':
                    readOps += ret[-1][consolidate]
                elif m.name == 'VolumeWriteOps':
                    writeOps += ret[-1][consolidate]
                elif m.name == 'VolumeReadBytes':
                    readBytes += ret[-1][consolidate]
                elif m.name == 'VolumeWriteBytes':
                    writeBytes += ret[-1][consolidate]
    return (readOps,writeOps,readBytes,writeBytes)


def getInstances( conn_kwargs ):
    '''
    Collect all the instances across all the
    systems (east, west, etc.). Leave out 
    terminated instances and None instances
    '''
    ec2conn = boto.connect_ec2(**conn_kwargs)
    ec2instances = []
    regions = ec2conn.get_all_regions()
    for region in regions:
        try:
            conn = region.connect(**conn_kwargs)
            for reservation in conn.get_all_instances():
                ec2instances.append([i for i in reservation.instances
                                     if i.id and i.state != 'terminated'])
        except boto.exception.EC2ResponseError, ex:
            #print "ERROR:%s" % ex.error_message
            continue
    return reduce(lambda x,y:x+y, ec2instances)


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
    
    work(opts,targetType)
    exit()


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)
