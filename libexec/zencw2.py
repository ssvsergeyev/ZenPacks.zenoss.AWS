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
    parser.add_option("--cachefile", dest="cachefile", default=CACHE_FILE)

    return parser.parse_args()




def main():
    opts, myargs = getOpts()
    pidfile = ""
    cwdaemon = ""
    # if pid file exists and process running exit
    if os.file.exists(pidfile):
        pid = open(pidfile).read()
        if os.process.running(pid):
            sys.exit(0)
        else:  # pid left behind, unclean shutdown
            os.file.remove(pidfile)
            os.system(cwdaemon)
    else:
        os.system(cwdaemon)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)
