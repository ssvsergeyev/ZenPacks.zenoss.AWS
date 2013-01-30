# check rrd files; create/delete
# query metrics, update rrd
# sleep?
import sys
import os
import fcntl
import time
from datetime import datetime, timedelta
import operator
import logging
import rrdtool
import pdb
from subprocess import call
logging.basicConfig()
log = logging.getLogger('ec2')
libDir = os.path.join(os.path.dirname(__file__), '../lib')
if os.path.isdir(libDir):
    sys.path.append(libDir)

import boto
logging.getLogger('boto').setLevel(logging.CRITICAL)

FIELD_NAMES = (
    'CPUUtilization',
    'NetworkIn',
    'NetworkOut',
    'DiskReadBytes',
    'DiskWriteBytes',
    'DiskReadOps',
    'DiskWriteOps',
    'EBSReadBytes',
    'EBSWriteBytes',
    'EBSReadOps',
    'EBSWriteOps',
    'EBSruntime'
)

conn_kwargs = {
    'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID', None),
    'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY', None),
}

_rrd_path = '/opt/zenoss/perf/Devices/EC2Manager'

def getInstances():
    '''
    Collect all the instances across all the
    systems (east, west, etc.). Leave out 
    terminated instances and None instances
    '''
    ec2conn = boto.connect_ec2(**conn_kwargs)
    ec2instances = []
    regions = ec2conn.get_all_regions()
    for region in regions:
        try:
            conn = region.connect(**conn_kwargs)
            for reservation in conn.get_all_instances():
                ec2instances.append([i for i in reservation.instances
                                     if i.id and i.state != 'terminated'])
        except boto.exception.EC2ResponseError, ex:
            #print "ERROR:%s" % ex.error_message
            continue
    return reduce(lambda x,y:x+y, ec2instances)

def update_instance_data():
    _instances = getInstances()
    instTypes = {}
    for i in _instances:
        if not instTypes.has_key(i.instance_type):
            instTypes[i.instance_type]=None
    _instTypes=instTypes.keys()
    return (_instances,_instTypes)

def check_rrd_fields(path):
    if not os.path.exists(path):
        os.makedirs(path)
    for field in FIELD_NAMES:
        if not os.path.exists(os.path.join(path,"zencw2_" + field + '.rrd')):
            create_rrd(path,field)

def create_rrd(path,field):
    filename = os.path.join(path,"zencw2_" + field + ".rrd")
    #(rrdtype of COUNTER, GAUGE, DERIVE, ABSOLUTE)
    rrdtype = 'GAUGE'
    rrdspec = 'DS:ds0:%s:900:U:U' % rrdtype
    #(agg_type of AVERAGE, MIN, MAX, ?)
    aggspecs = " ".join(['RRA:AVERAGE:0.5:1:600',
                         'RRA:AVERAGE:0.5:6:600',
                         'RRA:AVERAGE:0.5:24:600',
                         'RRA:AVERAGE:0.5:288:600',
                         'RRA:MAX:0.5:1:600'])
    #rrdtool.create(filename,"--step","300",rrdspec,aggspecs)
    os.system("rrdtool create %s" % " ".join([filename,"--step","300",rrdspec,aggspecs]))
    #call(['rrdtool', "create %s" % " ".join(filename,"--step","300",rrdspec,aggspecs)])

def update_rrd(field,subdir,value):
    cmd = "rrdtool update %s N:%f" % (os.path.join(_rrd_path,subdir,"zencw2_" + field + ".rrd"),value)
    print cmd
    os.system(cmd)



def query_with_backoff(metric,
                       start,
                       end,
                       consolidate,
                       units,
                       seconds):
    delay = 1
    tries = 4
    while(tries>0):
        try:
            ret=metric.query(start,end,consolidate,units,seconds)
            return ret
        except boto.exception.BotoServerError as ex:
            if ex.body.find('Throttling') > -1:
                time.sleep(delay)
                tries -= 1
                delay *= 2
            else:
                raise ex
    return None


class Cloudwatch():
    _instances = []
    _metrics = []
    _instTypes = []
    cwonn,ec2conn = None,None

    def __init__(self):
        self._instances,self._instTypes = update_instance_data()
        self.cwconn = boto.connect_cloudwatch(**conn_kwargs)
        self.ec2conn = boto.connect_ec2(**conn_kwargs)
        self.check_rrds()

    def server_loop(self):
        while(True):
            nexttime = datetime.utcnow() + timedelta(seconds=300)
            self.collect_instances()
            #self.collect_types()
            waittime = nexttime - datetime.utcnow()
            print waittime
            if waittime.total_seconds() > 0:
                time.sleep(waittime.total_seconds())

    def check_rrds(self):
        if not os.path.exists(_rrd_path):
            os.makedirs(_rrd_path)
        # check file for each field
        check_rrd_fields(_rrd_path)
        # directories for instanceTypes
        for itype in self._instTypes:
            check_rrd_fields(os.path.join(_rrd_path,"instanceTypes",itype))
        # directories for instances
        for inst in self._instances:
            check_rrd_fields(os.path.join(_rrd_path,"instances",inst.id))

    def getEBSVols(self):
        vols=self.ec2conn.get_all_volumes()
        vols=[v for v in vols if v.attachment_state() == 'attached']
        byInst = {}
        for v in vols:
            k=v.attach_data.instance_id
            byInst[k] = byInst.get(k,[]) + [v]
        return byInst

    def aggEBSmetrics(self,volumes,consolidate,units,seconds):
        runtime = datetime.utcnow()
        readOps = 0
        writeOps = 0
        readBytes = 0.0
        writeBytes = 0.0
        end = datetime.utcnow()
        start = end - timedelta(seconds=300+5)
        for v in volumes:
            mets=[m for m in self.cwconn.list_metrics(dimensions={'VolumeId':v.id})
                  if m.name in ['VolumeReadOps','VolumeWriteBytes','VolumeReadBytes','VolumeWriteOps']]
            for m in mets:
                ret=query_with_backoff(m,start,end,consolidate,units,seconds)
                if ret and len(ret)>0:
                    if m.name == 'VolumeReadOps':
                        readOps += ret[-1][consolidate]
                    elif m.name == 'VolumeWriteOps':
                        writeOps += ret[-1][consolidate]
                    elif m.name == 'VolumeReadBytes':
                        readBytes += ret[-1][consolidate]
                    elif m.name == 'VolumeWriteBytes':
                        writeBytes += ret[-1][consolidate]
        runtime = (datetime.utcnow() - runtime).total_seconds()
        return {'EBSReadOps':readOps,
            'EBSWriteOps':writeOps,
            'EBSReadBytes':readBytes,
            'EBSWriteBytes':writeBytes,'EBSruntime':runtime}
    
    def collect_instances(self,start=datetime.utcnow() - timedelta(seconds=305),
                          end=datetime.utcnow() - timedelta(seconds=5),
                          consolidate='Average',units="",seconds=300):
        volumes = self.getEBSVols()
        for i in self._instances:
            print( 'InstanceId:' + i.id)
            metrics = self.cwconn.list_metrics(namespace='AWS/EC2',dimensions={'InstanceId':i.id})
            if metrics and len(metrics) == 0:
                continue
            for m in [m2 for m2 in metrics if m2.name 
                  in ['CPUUtilization','NetworkIn','NetworkOut','DiskReadOps',
                      'DiskWriteOps','DiskReadBytes','DiskWriteBytes']]: 
                try:
                    ret = query_with_backoff(m, start, end, consolidate, units, seconds)
                    if ret and len(ret) > 0:
                        update_rrd(m.name,"instances/%s" % i.id,ret[-1][consolidate])
                except:
                        raise
                # get ebs metrics
            try:
                volstats = self.aggEBSmetrics(volumes[i.id],consolidate, units, seconds)
                for mname in volstats.keys():
                    update_rrd(mname,"instances/%s" % i.id,volstats[mname])
            except:
                    raise
    
    def collect_types(self,start=datetime.utcnow() - timedelta(seconds=305),
                      end=datetime.utcnow() - timedelta(seconds=5),
                      consolidate='Average',units="",seconds=300):
        for t in self._instTypes:
            output = 'InstanceType:' + t
            for m in [m2 for m2 in self.cwconn.list_metrics(namespace='AWS/EC2',dimensions={'InstanceType':t})
                      if m2.name in ['CPUUtilization','NetworkIn','NetworkOut','DiskReadOps',
                      'DiskWriteOps','DiskReadBytes','DiskWriteBytes']]:
                try:
                    ret = query_with_backoff(m, start, end, consolidate, units, seconds)
                    if ret and len(ret) > 0:
                        update_rrd(m.name,"instanceTypes/%s" % t,ret[-1][consolidate])
                except:
                        raise
            readOps = 0
            writeOps = 0
            readBytes = 0.0
            writeBytes = 0.0
            for i in [i2 for i2 in self._instances if i2.instance_type == t]:
                try:
                    volstats = self.aggEBSmetrics(volumes[i.id],consolidate, units, seconds)
                    readOps += volstats['DiskReadOps']
                    writeOps += volstats['DiskWriteOps']
                    readBytes += volstats['DiskRadBytes']
                    writeBytes += volstats['DiskWriteBytes']
                except:
                    continue
            update_rrd("EBSReadOps","instanceTypes/%s" % t,readOps)
            update_rrd("EBSWriteOps","instanceTypes/%s" % t,writeOps)
            update_rrd("EBSReadBytes","instanceTypes/%s" % t,readBytes)
            update_rrd("EBSWriteBytes","instanceTypes/%s" % t,writeBytes)



if __name__ == '__main__':
    try:
        cw = Cloudwatch()
        cw.server_loop()
    except Exception, e:
        log.exception(e)
        sys.stdout.write("CW FAIL: %s\n" % e)
        raise SystemExit(3)


##### TODO
#more closely match RRDUtil norms in rrdcreate (datasources, average defs)
#logging - debug logging & always log throttles
#error recovery -- lost connections, rrd missing, etc
#package into the zenpack (have zencw2 call it?  remove stuff that setupsup zencw2 and the rrds?)
#store metrics (not the values, the metrics)
#remove old instances
##subprocess out by region
#merge type & instance and thereby cut out repeat queries
