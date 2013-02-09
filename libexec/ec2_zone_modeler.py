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
import pickle
import pprint
import logging
logging.basicConfig(level=logging.CRITICAL,)

libDir = os.path.join(os.path.dirname(__file__), '../lib')
if os.path.isdir(libDir):
    sys.path.append(libDir)

import boto
import boto.exception

class EC2ZoneModeler(object):
    def __init__(self):
        self.getopts()
        try:
            if self.opts.file:
                self.conn_kwargs = {}
            else:
                if not self.opts.userkey:
                    print "ERROR:No access key ID has been provided"
                    sys.exit(1)
                elif not self.opts.privatekey:
                    print "ERROR:No secret access key has been provided"
                    sys.exit(1)
                self.conn_kwargs = {
                    'aws_access_key_id': self.opts.userkey,
                    'aws_secret_access_key': self.opts.privatekey,
                }
            conn = boto.connect_ec2(**self.conn_kwargs)
            self.regions = conn.get_all_regions()
        except boto.exception.EC2ResponseError, ex:
            print "ERROR:%s" % ex.error_message
            sys.exit(1)

    def makeMaps(self):
        ec2zones = []
        try:
            #import pdb
            #pdb.set_trace()
            zones = []
            for region in self.regions:
                conn=boto.ec2.connect_to_region(region.name,**self.conn_kwargs)
                zones += conn.get_all_zones()
            for z in zones:
                ec2zones.append({'zone_name':z.name,'region_name':z.region_name,
                                'state':z.state,'messages':z.messages})
        except boto.exception.EC2ResponseError, ex:
            print "ERROR:%s" % ex.error_message
            sys.exit(1)
        else:
            if self.opts.show:
                pprint.pprint(ec2zones)
            else:
                pickle.dump(ec2zones, sys.stdout)

    def getopts(self):
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-f", "--file", action="store_true", dest="file",
            help="use the boto config file for authentication")
        parser.add_option("-s", "--show", action="store_true", dest="show",
            help="use the boto config file for authentication")
        parser.add_option("-u","--userkey", dest="userkey",
                          default=os.environ.get('AWS_ACCESS_KEY_ID', None))
        parser.add_option("-p","--privatekey", dest="privatekey",
                          default=os.environ.get('AWS_SECRET_ACCESS_KEY', None))
        self.opts, self.args = parser.parse_args()


if __name__ == '__main__':
    zm = EC2ZoneModeler()
    zm.makeMaps()
