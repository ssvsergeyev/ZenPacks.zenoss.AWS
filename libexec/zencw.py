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
import datetime
import operator
import logging
logging.basicConfig()
log = logging.getLogger('ec2')

libDir = os.path.join(os.path.dirname(__file__), '../lib')
if os.path.isdir(libDir):
    sys.path.append(libDir)

import boto

def getMetrics(conn, identifier=None):
    metlist = []
    for met in conn.list_metrics():
        if getMetricId(met) == identifier:
            metlist.append(met)
    return metlist


def listMetrics(conn, identifier=None):
    metrics = getMetrics(conn, identifier)
    for met in metrics:
        sys.stdout.write("%s %s\n" % (met.name, getMetricId(met)))


def getMetricId(met):
    if met.dimensions is not None:
        for itype in ('InstanceId', 'InstanceType', 'ImageId'):
            if met.dimensions.get(itype, None) is not None:
                return met.dimensions.get(itype)
    return None


def buildData(metlist, units='', consolidate='Average', seconds=300):
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(seconds=seconds+5)
    out = {}
    for met in metlist:
        ret = met.query(start, end, consolidate, units, seconds)
        if len(ret) > 0:
            out[met.name] = ret[-1][consolidate]
    return out
    
    

def formatOutput(data):
    sys.stdout.write("CW OK |")
    for key, value in data.items():
        sys.stdout.write("%s=%s " % (key, value))
    
    
def getOpts():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--identifier", dest="identifier",
        help="AWS identifier, i-12345, ami-23423, m1.small")
    
    parser.add_option("-r", "--range", dest="range",
        help="time range to poll in seconds ", default=300, type='int')
    
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

    parser.add_option("-b", "--backoff", action="store_true", dest="backoff",                   
        help="sleep for a random amount of time before running the query")
        
    return parser.parse_args()


if __name__ == '__main__':
    opts, args = getOpts()
    if opts.backoff:
        import time, random
        time.sleep(random.uniform(0,1))
    try:
        conn_kwargs = {}
        if opts.userkey: conn_kwargs['aws_access_key_id'] = opts.userkey
        if opts.privatekey: conn_kwargs['aws_secret_access_key'] = opts.privatekey
        conn = boto.connect_cloudwatch(**conn_kwargs)
        data = buildData(getMetrics(conn, opts.identifier),opts.units,
                    opts.consolidate,opts.range)
        if not data:
            sys.stdout.write('CW FAIL: No output returned is the ID correct?\n')
            raise SystemExit(1)
        formatOutput(data)
    except SystemExit:
        raise
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(1)
