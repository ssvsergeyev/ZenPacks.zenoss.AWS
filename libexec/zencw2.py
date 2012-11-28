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
logging.basicConfig()
log = logging.getLogger('ec2')


libDir = os.path.join(os.path.dirname(__file__), '../lib')
if os.path.isdir(libDir):
    sys.path.append(libDir)

import boto
logging.getLogger('boto').setLevel(logging.CRITICAL)

#monkeypatch the requestmethod so we can count how many requests are being made
from boto import connection
oldMethod = connection.AWSAuthConnection.make_request
connection.AWSAuthConnection.mycounter = 0
def myCountingMethod(self, method, path, headers=None, data='', host=None,
                     auth_path=None, sender=None):
    connection.AWSAuthConnection.mycounter += 1
    return oldMethod(self, method, path, headers, data, host, auth_path, sender)
connection.AWSAuthConnection.make_request = myCountingMethod

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


def buildData(opts, stats):
    import time
    units = opts.units
    consolidate = opts.consolidate
    seconds = opts.range

    conn_kwargs = {
        'aws_access_key_id': opts.userkey,
        'aws_secret_access_key': opts.privatekey,
    }
   
    querystart = time.time() 
    instances = getCurrentInstances( conn_kwargs )

    conn = boto.connect_cloudwatch(**conn_kwargs)
    metlist = []
    tmp = conn.list_metrics()
    metlist = tmp
    nt = metlist.next_token
    resultsets = 0
    if not stats:
        stats = {}
    #allocate 1/5 of the runtime to fetching the avail metrics
    prevResultsets = stats.get("resultsetcount", 10.0)
    if prevResultsets == 0:
        prevResultsets = 10.0
    metricWaitTime = (opts.range * 0.2) / prevResultsets
    if opts.logseverity > 0:
        print "previous result set count was %f" % prevResultsets
        print "wait time is %f" % metricWaitTime

    while nt:
        resultsets += 1
        if opts.logseverity > 0:
            print("using token: %s" % nt)
        time.sleep(metricWaitTime)
        tmp = conn.list_metrics(next_token=nt)
        metlist += tmp
        nt = tmp.next_token
   
    end = datetime.utcnow()
    start = end - timedelta(seconds=seconds+5)
    mdict = dict()
    counter = 1
    metriccounter = 0
    prevMetricCount = stats.get("metriccount", 1000.0)
    metricCountWaitTime = (opts.range * 0.6) / prevMetricCount

    if opts.logseverity > 0:
        print "previous metric count was %f" % prevMetricCount
        print "wait time is %f" % metricCountWaitTime

    for met in metlist:
        if filterMetricTypes( met, instances):
            time.sleep(metricCountWaitTime)
            counter += 1
            metriccounter += 1
            if opts.logseverity > 0:
                print "fetching: %r" % met
            id = getMetricId(met)
            instvalues = mdict.setdefault(id, [])
            ret = met.query(start, end, consolidate, units, seconds)
            if len(ret) > 0:
                instvalues.append((met.name, ret[-1][consolidate]))
        else:
            if opts.logseverity > 0:
                print "excluding: %r" % met
    queryend = time.time()
   
    stats = dict(
        resultsetcount = resultsets, 
        metriccount = metriccounter,
        querytime = queryend - querystart
    )

    return stats, mdict


def filterMetricTypes( met, instances):

    #filter out decommissioned instances
    instanceId = met.dimensions.get('InstanceId')
    if instanceId:
        return instanceId in instances
    else:
        #exclude metric types we don't do
        #anything with, in order to preserve calls to Amazon
        for mtype in ('ImageId', 'VolumeId'):
            if met.dimensions.get(mtype): 
                return False
        return True


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


def getMetricId(met):
    if met.dimensions is not None:
        for itype in ('InstanceId', 'InstanceType', 'ImageId', 'VolumeId'):
            if met.dimensions.get(itype, None) is not None:
                return "%s:%s" % (itype, met.dimensions.get(itype))
    return "Manager:0"


def output(requestInstanceType, data):
    # print out our data using the Nagios API format (for zencommand)
    for instId, instData in data.items():
        # this is for backwards compatability.
        # old interface used Instance now it must be InstanceId
        if requestInstanceType == "Instance":
            requestInstanceType += "Id"
        if str(instId.split(':')[0]) != requestInstanceType:
            continue
        outData = []
        for dpvalue in instData:
            outData.append(dpvalue)
        sortedOutData = [instId]
        for dpname in DP_NAMES:
            for dptuple in outData:
                if dpname in dptuple:
                    sortedOutData.append("%s %0.2f" % (dptuple))
        print " ".join(sortedOutData)



def buildCache(opts, stats):
    # touch the file if it doesn't exist
    if not os.path.exists(opts.cachefile):
        open(opts.cachefile, 'w').close()
        open(STATS_FILE, 'w').close()

    # now rebuild the file if it's of 0 size or old
    if (os.path.getsize(opts.cachefile) == 0 or
        os.path.getctime(opts.cachefile) < time.time() - CACHE_LIFE):
        if opts.logseverity > 0:
            print('rebuilding the cloud watch cache file')
        fd = open(opts.cachefile, 'w')
        sfd = open(STATS_FILE, 'w')
        fcntl.lockf(fd, fcntl.LOCK_EX)
        fcntl.lockf(sfd, fcntl.LOCK_EX)

        stats, mdict = buildData(opts, stats)
        stats['requestcount'] = connection.AWSAuthConnection.mycounter
        pickle.dump(mdict, fd)
        pickle.dump(stats, sfd)

        fcntl.lockf(fd, fcntl.LOCK_UN)
        fcntl.lockf(sfd, fcntl.LOCK_UN)
        fd.close()
        sfd.close()
    return stats


def readCache(cacheFile):
    # read the file using a shared lock
    # this will block if buildCache is in the process of a cache refresh
    if not os.path.exists(cacheFile):
        return None
    with open(cacheFile, 'r') as fd:
        fcntl.lockf(fd, fcntl.LOCK_SH)
        try:
            return pickle.load(fd)
        except:
            return None
        finally:
            fcntl.lockf(fd, fcntl.LOCK_UN)


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

    stats = readCache(STATS_FILE)
    stats = buildCache(opts, stats)
    if stats and opts.logseverity > 0:
        print "Total Request Count  : %i" % stats['requestcount']
        print "Total Resultset Count: %i" % stats['resultsetcount']
        print "Total Query Time     : %i" % stats['querytime']
        print "Total Metric Count   : %i" % stats['metriccount']

    data = readCache(opts.cachefile)
    #print targetType
    #print data
    output(targetType, data)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)
