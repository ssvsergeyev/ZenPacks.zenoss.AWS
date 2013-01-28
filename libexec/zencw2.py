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

if __name__ == '__main__':
    try:
        os.system("python ../daemons/cloudwatch.py")
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)
