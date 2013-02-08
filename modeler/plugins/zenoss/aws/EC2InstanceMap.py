##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


__doc__="""EC2InstanceMap
Model Amazon WS EC2 information
"""

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.ZenUtils.Utils import zenPath
from twisted.internet.utils import getProcessOutput
import re, os, pdb


class EC2InstanceMap(PythonPlugin):
    
    transport = "python"
    maptype = "EC2InstanceMap"

    deviceProperties = PythonPlugin.deviceProperties + ('access_id', 'zEC2Secret')
    
    def findPath(self):
        path = []
        for p in __file__.split(os.sep):
            if p == 'modeler': break
            path.append(p)
        return os.sep.join(path)
        
    def collect(self, device, log):
        path = self.findPath()
        log.info("running zenec2modeler plugin")
        cmd = path+'/libexec/zenec2modeler.py'
        py = zenPath("bin","python")
        args = (cmd,)
        os.environ['AWS_ACCESS_KEY_ID'] = device.access_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = device.zEC2Secret
        ret = getProcessOutput(py, args, os.environ)
        return ret

    def process(self, device, results, log):
        om = self.objectMap()
        if results.startswith('ERROR:'):
            log.warn(results.replace('ERROR:', ''))
        else:
            om.setInstances = results
        return om
