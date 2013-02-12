##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


import logging
log = logging.getLogger('zen.AWSFacade')

from zope.interface import implements

from Products.Zuul.facades import ZuulFacade
from ZenPacks.zenoss.ZenAWS.interfaces import IAWSFacade


class AWSFacade(ZuulFacade):
    implements(IAWSFacade)
    """
    Facade for the AWS ZenPack
    """

    def configure(self, access_id, secret,
                  devicePath='', devicePathForWindows=''):
        # There is one special host 'EC2Manager' which *MUST* exist
        mgrPath = '/zport/dmd/Devices/AWS/EC2/devices/EC2Manager'
        mgr = self._dmd.restrictedTraverse(mgrPath)
        mgr.manage_editEC2Manager(access_id, secret,
                           devicePath, devicePathForWindows)
