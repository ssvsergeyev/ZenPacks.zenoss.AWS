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

from zope.schema.vocabulary import SimpleVocabulary

from Products.Zuul.form import schema
from Products.Zuul.utils import ZuulMessageFactory as _t
from Products.Zuul.interfaces.actions import  IInfo


class IAWSEmailHostActionContentInfo(IInfo):

    email_from = schema.Text(
        title       = _t(u'From Address for Emails'),
        description = _t(u'The user from which the e-mail originated on the Zenoss server.'),
        default = u'root@localhost.localdomain'
    )

    aws_name = schema.Text(
        title       = _t(u'AWS Account Name'),
        description = _t(u'Simple Mail Transport Protocol (aka E-mail server).'),
    )

    aws_access_key = schema.Text(
        title       = _t(u'AWS Access Key'),
        description = _t(u'Simple Mail Transport Protocol (aka E-mail server).'),
    )

    aws_secret_key = schema.Text(
        title       = _t(u'AWS Secret Key'),
        description = _t(u'Simple Mail Transport Protocol (aka E-mail server).'),
    )
