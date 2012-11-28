##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


"""
"""

from Products.ZenRRD.ComponentCommandParser import ComponentCommandParser

class instances(ComponentCommandParser):

    componentSplit = '\n'

    componentScanner = r'^\S+:(?P<component>\S+)'

    scanners = [
        r'.*CPUUtilization (?P<CPUUtilization>[\d\.]+).*',
        r'.*NetworkIn (?P<NetworkIn>[\d\.]+).*',
        r'.*NetworkOut (?P<NetworkOut>[\d\.]+).*',
        r'.*DiskReadBytes (?P<DiskReadBytes>[\d\.]+).*',
        r'.*DiskWriteBytes (?P<DiskWriteBytes>[\d\.]+).*',
        r'.*DiskReadOps (?P<DiskReadOps>[\d\.]+).*',
        r'.*DiskWriteOps (?P<DiskWriteOps>[\d\.]+).*'
        ]

    componentScanValue = 'id'
