##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenModel.DeviceComponent import DeviceComponent
from Products.ZenRelations.RelSchema import ToOne, ToMany, ToManyCont
from Products.ZenModel.ZenossSecurity import ZEN_VIEW
from Products.Jobber.exceptions import NoSuchJobException

class EC2Instance(DeviceComponent, ManagedEntity):
    """
    A DMD Device that represents a group of VMware hosts 
    that can run virtual devices.
    """

    meta_type = "EC2Instance"
    
    instance_id = ""
    dns_name = ""
    aws_name = ""
    public_dns_name = ""
    private_dns_name = ""
    private_ip = ""
    image_id = ""
    instance_type = ""
    kernel_id = ""
    key_name = ""
    launch_time = ""
    placement = ""
    ramdisk = ""
    deviceId = ""
    state = ""
    region = ""
    platform = ""
    _discoveryState = 10
    _discoveryJobId = None
    _deviceProdStatePreStop = 1000
    
    _properties = (
        {'id':'instance_id',        'type':'string', 'mode':'w'},
        {'id':'dns_name',           'type':'string', 'mode':'w'},
        {'id':'aws_name',           'type':'string', 'mode':'w'},
        {'id':'public_dns_name',    'type':'string', 'mode':'w'},
        {'id':'private_dns_name',   'type':'string', 'mode':'w'},
        {'id':'private_ip',         'type':'string', 'mode':'w'},
        {'id':'image_id',           'type':'string', 'mode':'w'},
        {'id':'instance_type',      'type':'string', 'mode':'w'},
        {'id':'kernel_id',          'type':'string', 'mode':'w'},
        {'id':'key_name',           'type':'string', 'mode':'w'},
        {'id':'launch_time',        'type':'string', 'mode':'w'},
        {'id':'placement',          'type':'string', 'mode':'w'},
        {'id':'ramdisk',            'type':'string', 'mode':'w'},
        {'id':'deviceLink',         'type':'string', 'mode':'w'},
        {'id':'deviceName',         'type':'string', 'mode':'w'},
        {'id':'deviceId',           'type':'string', 'mode':'w'},
        {'id':'state',              'type':'string', 'mode':'w'},
        {'id':'region',             'type':'string', 'mode':'w'},
        {'id':'platform',           'type':'string', 'mode':'w'},
    )


    _relations = (
        ('manager', ToOne(ToManyCont, 
            "ZenPacks.zenoss.ZenAWS.EC2Manager", "instances")),
        ('instanceType', ToOne(ToMany, 
            "ZenPacks.zenoss.ZenAWS.EC2InstanceType", "instances")),
    )

    factory_type_information = (
        {
            'immediate_view' : 'ec2InstanceStatus',
            'actions'        :
            (
                { 'id'            : 'perfServer'
                , 'name'          : 'Graphs'
                , 'action'        : 'viewDevicePerformance'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'status'
                , 'name'          : 'Status'
                , 'action'        : 'ec2InstanceStatus'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'events'
                , 'name'          : 'Events'
                , 'action'        : 'viewEvents'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'perfConf'
                , 'name'          : 'Template'
                , 'action'        : 'objTemplates'
                , 'permissions'   : ("Change Device", )
                },                
            )
         },
        )
        
    def device(self):
        return self.manager()
        
        
    def monitored(self):
        if self.state == 'running':
            return super(EC2Instance, self).monitored()
        return False
        
        
    def name(self):
        return self.titleOrId()
    
    def isDiscoveryPending(self):
        # check if we have a job pending
        if self._discoveryJobId:
            try:
                jobStatus = self.dmd.JobManager.getJob(self._discoveryJobId)
                if jobStatus and jobStatus.finished is None:
                    return True
            except NoSuchJobException:
                pass
        return False
    
    def updateFromDict(self, propDict):
        for k, v in propDict.items():
            if k == 'monitored': continue
            setattr(self, k, v)
            
    def getDeviceLink(self):
        if self.deviceId:
            rdev = self.findDeviceByIdExact(self.deviceId)
            if rdev:
                return rdev.getPrimaryUrlPath()
        return ""
    
    def getDeviceName(self):
        if self.deviceId:
            rdev = self.findDeviceByIdExact(self.deviceId)
            if rdev:
                return rdev.titleOrId()
        return ""
