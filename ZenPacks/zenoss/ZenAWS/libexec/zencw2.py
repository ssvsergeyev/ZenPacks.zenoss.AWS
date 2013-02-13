#!/usr/bin/env python
##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################

import subprocess
import sys
import os
import logging
logging.basicConfig()
log = logging.getLogger('ec2')
libDir = os.path.join(os.path.dirname(__file__), '../lib')
if os.path.isdir(libDir):
    sys.path.append(libDir)
logging.getLogger('boto').setLevel(logging.CRITICAL)


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
    return parser.parse_args()


ddir = os.path.join(os.path.dirname(__file__), '../daemons')
pidfile = os.path.join(ddir,'cloudwatch.pid')
daemon = os.path.join(ddir,'cloudwatch.py')

def main():
    opts, myargs = getOpts()
    targetType = myargs[0][3:]
    os.environ['AWS_ACCESS_KEY_ID'] = opts.userkey
    os.environ['AWS_SECRET_ACCESS_KEY'] = opts.privatekey
    # i chopped this down so that there wouldn't be a race condition with CWMonitor calling 4 at once
    if targetType not in ('Manager', 'Daemon'):
        print "zencw2.py command [options] command must be of type " \
              "EC2Manager, EC2Instance, EC2InstanceType or EC2ImageId"
        raise SystemExit(3)
    # if pid file exists and process running exit
    #for region in boto.ec2.regions():
    #    regionpidfile = pidfile + "-" + str(region)
    if os.path.exists(pidfile):
        # skip pid handling and all that -- going to run seperate processes for each region
        pass
        # Popen.pid
        pid = open(pidfile).read()
        if os.process.running(pid):
            sys.exit(0)
        else:  # pid left behind, unclean shutdown
            os.unlink(pidfile)
	    fh=open(pidfile,'w')
            fh.write('pid')
	    fh.close()
            os.system("python %s &" % daemon)
    else:
	fh=open(pidfile,'w')
	fh.write('pid')
	fh.close()
        os.system("python %s &" % daemon)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)
