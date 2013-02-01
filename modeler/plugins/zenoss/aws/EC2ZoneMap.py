from Products.ZenUtils.Utils import zenPath
from twisted.internet.utils import getProcessOutput
import re, os


class EC2ZoneMap(PythonPlugin):
    
    transport = "python"
    maptype = "EC2ZoneMap"

    deviceProperties = PythonPlugin.deviceProperties + ('access_id', 'zEC2Secret')
    
    def findPath(self):
        path = []
        for p in __file__.split(os.sep):
            if p == 'modeler': break
            path.append(p)
        return os.sep.join(path)
        
    def collect(self, device, log):
        path = self.findPath()
        log.info("running ec2zonemodeler plugin")
        cmd = path+'/libexec/ec2_zone_modeler.py'
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
