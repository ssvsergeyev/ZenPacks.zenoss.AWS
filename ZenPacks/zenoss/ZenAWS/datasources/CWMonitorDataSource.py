##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

__doc__ = '''CWMonitorDataSource.py

Defines datasource for CWMonitor
'''

from Globals import InitializeClass

from Products.ZenUtils.ZenTales import talesEvalStr

import Products.ZenModel.BasicDataSource as BasicDataSource
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from AccessControl import ClassSecurityInfo, Permissions
from Products.ZenUtils.ZenTales import talesCompile, getEngine

import os


class CWMonitorDataSource(ZenPackPersistence,
                                BasicDataSource.BasicDataSource):

    CW_MONITOR = 'CWMonitor'

    ZENPACKID = 'ZenPacks.zenoss.ZenAWS'

    sourcetypes = (CW_MONITOR,)
    sourcetype = CW_MONITOR

    timeout = 30
    eventClass = '/Cmd/Fail'

    parser = 'ZenPacks.zenoss.ZenAWS.parsers.ec2.instances'

    cycletime = 300

    _properties = BasicDataSource.BasicDataSource._properties + (
        {'id': 'timeout', 'type': 'int', 'mode': 'w'},
    )

    factory_type_information = (
    {
        'immediate_view': 'editCWMonitorDataSource',
        'actions':
        (
            {'id': 'edit',
            'name': 'Data Source',
            'action': 'editCWMonitorDataSource',
            'permissions': (Permissions.view, ),
            },
        )
    },
    )

    security = ClassSecurityInfo()

    def __init__(self, id, title=None, buildRelations=True):
        BasicDataSource.BasicDataSource.__init__(self, id, title,
                buildRelations)

    def manage_afterAdd(self, item, container):
        if self.rrdTemplate().id == 'EC2Manager':
            self.parser = 'ZenPacks.zenoss.ZenAWS.parsers.ec2.manager'

    def getDescription(self):
        if self.sourcetype == self.CW_MONITOR:
            return "Collect CloudWatch statistics from an entities of type " \
            "Instance InstanceType and Global Account"
        return BasicDataSource.BasicDataSource.getDescription(self)

    def useZenCommand(self):
        return True

    def getCommand(self, context):
        parts = ['zencw2.py', self.rrdTemplate().id]
        parts.append('-u ${device/access_id}')
        parts.append('-p ${device/zEC2Secret}')
        if self.cycletime:
            parts.append('-r %s' % self.cycletime)
        cmd = ' '.join(parts)
        cmd = BasicDataSource.BasicDataSource.getCommand(self, context, cmd)
        return cmd

    def checkCommandPrefix(self, context, cmd):
        if self.usessh:
            return os.path.join(context.zCommandPath, cmd)
        zp = self.getZenPack(context)
        return zp.path('libexec', cmd)

    def addDataPoints(self):
        dps = (
            ('CPUUtilization', 'GAUGE'),
            ('NetworkIn', 'GAUGE'),
            ('NetworkOut', 'GAUGE'),
            ('DiskWriteBytes', 'GAUGE'),
            ('DiskReadBytes', 'GAUGE'),
            ('DiskWriteOps', 'GAUGE'),
            ('DiskReadOps', 'GAUGE'),
            ('VolumeReadOps', 'GAUGE'),
            ('VolumeWriteOps', 'GAUGE'),
            ('VolumeReadBytes', 'GAUGE'),
            ('VolumeWriteBytes', 'GAUGE')
        )
        for dpd in dps:
            dp = self.manage_addRRDDataPoint(dpd[0])
            dp.rrdtype = dpd[1]
            dp.rrdmin = 0

    def zmanage_editProperties(self, REQUEST=None):
        '''validation, etc'''
        if REQUEST:
            # ensure default datapoint didn't go away
            self.addDataPoints()
            # and eventClass
            if not REQUEST.form.get('eventClass', None):
                REQUEST.form['eventClass'] = self.__class__.eventClass
        return BasicDataSource.BasicDataSource.zmanage_editProperties(self,
                REQUEST)

InitializeClass(CWMonitorDataSource)
