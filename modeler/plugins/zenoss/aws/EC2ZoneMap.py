__doc__="""EC2ZoneMap
Model Amazon WS EC2 information
"""

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.ZenUtils.Utils import zenPath
from twisted.internet.utils import getProcessOutput
import re, os, pdb, pickle


class EC2ZoneMap(PythonPlugin):
    
    transport = "python"
    maptype = "EC2ZoneMap"
    relname = 'zones'
    modname = 'ZenPacks.zenoss.ZenAWS.EC2Zone'

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
	#pdb.set_trace()
        if results.startswith('ERROR:'):
            log.warn(results.replace('ERROR:', ''))
	results = pickle.loads(results)
        #rm = self.relMap()
	#for r in results:
	#    rm.append(self.objectMap({'id':r['name'],'name':r['name'],'state':r['state'],'messages':r['messages']}))
        #return rm
