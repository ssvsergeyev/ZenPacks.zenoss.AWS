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
from Products.ZenRRD.CommandParser import CommandParser

class manager(CommandParser):

    def processResults(self, cmd, result):
        """
        """
        dps = dict([(dp.id, dp) for dp in cmd.points])
        
        parts = cmd.result.output.split()[1:]
        for i in range(0, len(parts), 2):
            dpname = parts[i]
            if dpname in dps:
                result.values.append((dps[parts[i]], float(parts[i+1])))
        return result
