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

from Products.Zuul.infos.actions import ActionFieldProperty
from Products.Zuul.infos import InfoBase
from ZenPacks.zenoss.AWS.interfaces import IAWSEmailHostActionContentInfo


class AWSEmailHostActionContentInfo(InfoBase):
    implements(IAWSEmailHostActionContentInfo)

    body_content_type = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'body_content_type')
    subject_format = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'subject_format')
    body_format = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'body_format')
    clear_subject_format = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'clear_subject_format')
    clear_body_format = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'clear_body_format')
    email_from = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'email_from')
    aws_account_name = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'aws_account_name')
    aws_region = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'aws_region')
    aws_access_key = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'aws_access_key')
    aws_secret_key = ActionFieldProperty(IAWSEmailHostActionContentInfo, 'aws_secret_key')
