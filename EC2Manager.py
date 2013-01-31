##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2009, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


import re
import pickle
import logging
log = logging.getLogger('ec2')

from Globals import InitializeClass
from Products.ZenModel.Device import Device, manage_createDevice
from Products.ZenModel.Exceptions import DeviceExistsError
from Products.ZenModel.ZenossSecurity import ZEN_VIEW
from Products.ZenRelations.RelSchema import ToOne, ToManyCont

from ZenPacks.zenoss.ZenAWS.EC2Instance import EC2Instance
from ZenPacks.zenoss.ZenAWS.EC2InstanceType import EC2InstanceType

DISCOVER = 10
LINK = 20
COMPLETED = 30

isWindowsPlatform = re.compile(r"\bwindows\b", re.IGNORECASE).search

class EC2Manager(Device):
    """
    A DMD Device that represents a group of VMware hosts
    that can run virtual devices.
    """
    meta_type = portal_type = "EC2Manager"

    instid = ''
    access_id = ''
    devicePath = ''
    devicePathForWindows = ''

    _my_pickle_data = ''

    _properties = Device._properties + (
        {'id':'access_id',  'type':'string', 'mode':'w'},
        {'id':'devicePath', 'type':'string', 'mode':'w'},
        {'id':'devicePathForWindows', 'type':'string', 'mode':'w'},
    )

    _relations = Device._relations + (
        ('instances', ToManyCont(ToOne,
            "ZenPacks.zenoss.ZenAWS.EC2Instance", "manager")),
        ('instanceTypes', ToManyCont(ToOne,
            "ZenPacks.zenoss.ZenAWS.EC2InstanceType", "manager")),
        ('zones', ToManyCont(ToOne,
            "ZenPacks.zenoss.ZenAWS.EC2Zone", "manager")),
        )

    factory_type_information = (
        {
            'immediate_view' : 'devicedetail',
            'actions'        :
            (
                { 'id'            : 'editEC2Manager'
                , 'name'          : 'Configure EC2'
                , 'action'        : 'editEC2Manager'
                , 'permissions'   : ("Change Device",)
                },
                { 'id'            : 'instances'
                , 'name'          : 'Instances'
                , 'action'        : 'viewInstances'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'instanceTypes'
                , 'name'          : 'Instance Types'
                , 'action'        : 'viewInstanceTypes'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'zones'
                , 'name'          : 'Zones'
                , 'action'        : 'viewZones'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'events'
                , 'name'          : 'Events'
                , 'action'        : 'viewEvents'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'perfServer'
                , 'name'          : 'Graphs'
                , 'action'        : 'viewDevicePerformance'
                , 'permissions'   : (ZEN_VIEW, )
                }
            )
         },
        )

    def __init__(self, id, buildRelations=True):
        super(EC2Manager, self).__init__(id, buildRelations)


    def setInstances(self, instPickle):
        """
        This method is called by the modeler.
        """
        self._my_pickle_data = instPickle
        instances = pickle.loads(instPickle)
        self._setInstances(instances)

    def _setInstances(self, instances):
        """
        Use this method if tests are ever written.
        """
        instids = self.instances.objectIdsAll()
        for instdict in instances:
            instid = str(instdict['id'])
            deviceId = "aws-" + instid
            if instid in instids: instids.remove(instid)
            inst = self._createOrUpdateInstance(instid, instdict)
            itype = self._createOrUpdateInstanceTypes(inst, instdict)
            if inst.instanceType() != itype:
                inst.instanceType.removeRelation()
                inst.instanceType.addRelation(itype)

            if inst.state == 'running':

                devicePath = self._getDevicePath(instdict)

                if inst._discoveryState == DISCOVER and inst.dns_name:
                    
                    if devicePath:
                        # see if device already exists
                        if self.findDeviceByIdExact(deviceId):
                            # device was found, just link
                            rdev = self._linkInstancesToDevices(inst, deviceId)
                            if rdev:
                                log.debug('linked inst %s to existing device %s',
                                            inst.id, rdev.id)
                                inst._discoveryState = COMPLETED
                            else:
                                log.debug('failed to link %s to an existing device %s',
                                          inst.id, deviceId)
                        else:
                            # device was not found, let zendisc create one
                            collector = self.getPerformanceServer()
                            inst._discoveryJobId = collector._executeZenDiscCommand(
                                                    inst.dns_name,
                                                    devicePath,
                                                    self.getPerformanceServerName(),
                                                    background=True).id
                            log.debug('started auto-discovery for %s', inst.id)
                            inst._discoveryState = LINK
                    else:
                        # don't try to link device, if no device classes were set
                        self._discoveryState = COMPLETED
                        log.debug('skipped auto-discovery for %s: devicePath not set',
                                  inst.id)

                elif inst._discoveryState == LINK:
                    rdev = self._linkInstancesToDevices(inst, deviceId)
                    if rdev:
                        log.debug('linked inst %s to device %s',
                                    inst.id, rdev.id)
                        inst._discoveryState = COMPLETED
                    else:
                        if inst.isDiscoveryPending():
                            log.debug('failed to link %s to a device, device creation is pending', inst.id)
                        else:
                            collector = self.getPerformanceServer()
                            inst._discoveryJobId = \
                                collector._executeZenDiscCommand(
                                inst.dns_name,
                                devicePath,
                                self.getPerformanceServerName(),
                                background=True).id
                            log.debug('restarted auto-discovery for %s', inst.id)
                            
                elif inst._discoveryState == COMPLETED and devicePath and \
                    self.findDeviceByIdExact(deviceId) is None:

                    collector = self.getPerformanceServer()
                    inst._discoveryJobId = collector._executeZenDiscCommand(
                                            inst.dns_name,
                                            devicePath,
                                            self.getPerformanceServerName(),
                                            background=True).id
                    log.debug('started auto-discovery for %s. ' +
                              'Device was deleted or got new mapping', inst.id)
                    inst._discoveryState = LINK


            elif inst.state == 'stopped' and inst._discoveryState != LINK:
                rdev = self.findDeviceByIdExact(deviceId)
                if rdev:
                    inst._deviceProdStatePreStop = rdev.productionState
                    rdev.setProdState(-1)
                    log.debug('pausing device %s after it was stopped',
                                rdev.id)
                inst._discoveryState = LINK

        for instid in instids:
            deviceId = "aws-" + instid
            rdev = self.findDeviceByIdExact(deviceId)
            if rdev:
                log.debug('deleting device %s after inst %s was terminated',
                            rdev.id, instid)
                rdev.deleteDevice()
            self.instances._delObject(instid)


    def getInstances(self):
        """
        return the last pickle sent to see if anything actually changed.
        """
        return [] # return None for now until we debug the optimization below
        #if [ inst for inst in self.instances() \
        #    if inst._discoveryState == COMPLETED ]:
        #    return self._my_pickle_data


    def _linkInstancesToDevices(self, inst, deviceId):
        if not inst.id.startswith('i-'): return

        try:
            import socket
            ipaddr = socket.gethostbyname(inst.dns_name)
        except socket.gaierror, e:
            # if we don't have an ip we need to bail
            return

        rdev = self.findDeviceByIdExact(deviceId)
        if rdev:
            rdev.title = inst.dns_name
            rdev.manageIp = ipaddr
            rdev.setProdState(inst._deviceProdStatePreStop)
            inst.deviceId = rdev.id
        else:
            rdev = self.findDeviceByIdOrIp(ipaddr)
            if ipaddr and rdev and rdev.manageIp == ipaddr:
                rlink = "<a href='%s'>%s</a>" % (inst.getPrimaryUrlPath(),
                                                inst.id)
                rdev.setZenProperty('zLinks', rlink)
                rdev.renameDevice(deviceId)
                rdev.setLocation("/"+str(inst.placement.replace('-','/')))
                rdev.title = inst.dns_name
                inst.deviceId = rdev.id
        return rdev



    def _createOrUpdateInstance(self, instid, properties):
        inst = self.instances._getOb(instid, None)
        if inst is None:
            inst = EC2Instance(instid)
            self.instances._setObject(instid, inst)
            inst = self.instances._getOb(instid)
        inst.updateFromDict(properties)
        inst.index_object() # reindex because updateFromDict will have set state
        return inst


    def _createOrUpdateInstanceTypes(self, instance, instdict):
        itypename = str(instdict['instance_type'])
        itype = self.instanceTypes._getOb(itypename, None)
        if itype is None:
            itype = EC2InstanceType(itypename)
            self.instanceTypes._setObject(itypename, itype)
            itype = self.instanceTypes._getOb(itypename)
        return itype



    def manage_editEC2Manager(self, access_id, secret, devicePath="", devicePathForWindows="", **kwargs):
        """edit a ec2manager"""
        self.access_id = access_id
        self.devicePath = devicePath
        self.devicePathForWindows = devicePathForWindows
        if secret and secret != self.zEC2Secret:
            self.setZenProperty('zEC2Secret', secret)
        return super(EC2Manager, self).manage_editDevice(
            REQUEST=self.REQUEST, **kwargs)
        
    def manage_resetInstancesState(self):
        instids = self.instances.objectIdsAll()
        for instid in instids:
            inst = self.instances._getOb(instid, None)
            if inst:
                inst._discoveryState = DISCOVER
                inst.index_object()
            
    def _getDevicePath(self, instdict):
        # determine platform
        devicePath = None
        if instdict['platform'] and isWindowsPlatform(instdict['platform']):
            # @TODO use products key to determine SQL Server, etc
            devicePath = self.devicePathForWindows
        else:
            devicePath = self.devicePath
        return devicePath


InitializeClass(EC2Manager)
