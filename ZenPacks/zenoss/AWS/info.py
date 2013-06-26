###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

import Globals

from zope.interface import implements

from Products.Zuul.infos.actions import EmailActionContentInfo, ActionFieldProperty
from Products.Zuul.infos import InfoBase
from ZenPacks.zenoss.AWS.interfaces import IAWSEmailHostActionContentInfo


class AWSEmailHostActionContentInfo(InfoBase):
    implements(IAWSEmailHostActionContentInfo)

    email_from = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'email_from')
    #host = ActionFieldProperty(IAltEmailHostActionContentInfo, 'host')
    #port = ActionFieldProperty(IAltEmailHostActionContentInfo, 'port')
    #useTls = ActionFieldProperty(IAltEmailHostActionContentInfo, 'useTls')
    #user = ActionFieldProperty(IAltEmailHostActionContentInfo, 'user')
    #password = ActionFieldProperty(IAltEmailHostActionContentInfo, 'password')

