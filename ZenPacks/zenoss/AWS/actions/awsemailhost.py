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

import logging
log = logging.getLogger("zen.useraction.actions")

import Globals

from zope.interface import implements

from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

from Products.ZenUtils.Utils import sendEmail
from Products.ZenModel.interfaces import IAction, IProvidesEmailAddresses
from Products.ZenModel.actions import IActionBase, TargetableAction, processTalSource, _signalToContextDict

from ZenPacks.zenoss.AWS.AWSEmail import IAWSEmailHostActionContentInfo
from ZenPacks.zenoss.AWS.utils import addLocalLibPath

addLocalLibPath()
import boto.ses


class AWSEmailHostAction(IActionBase, TargetableAction):
    implements(IAction)

    id = 'awsemailhost'
    name = 'AWS Email Host'
    actionContentInfo = IAWSEmailHostActionContentInfo

    def __init__(self):
        super(AWSEmailHostAction, self).__init__()

    def setupAction(self, dmd):
        self.guidManager = GUIDManager(dmd)

    def executeOnTarget(self, notification, signal, targets):
        log.debug("Executing %s action for targets: %s", self.name, targets)
        self.setupAction(notification.dmd)

        data = _signalToContextDict(signal, self.options.get('zopeurl'), notification, self.guidManager)
        if signal.clear:
            log.debug('This is a clearing signal.')
            subject = processTalSource(notification.content['clear_subject_format'], **data)
            body = processTalSource(notification.content['clear_body_format'], **data)
        else:
            subject = processTalSource(notification.content['subject_format'], **data)
            body = processTalSource(notification.content['body_format'], **data)

        log.debug('Sending this subject: %s' % subject)
        log.debug('Sending this body: %s' % body)

        plain_body = MIMEText(self._stripTags(body))
        email_message = plain_body

        if notification.content['body_content_type'] == 'html':
            email_message = MIMEMultipart('related')
            email_message_alternative = MIMEMultipart('alternative')
            email_message_alternative.attach(plain_body)

            html_body = MIMEText(body.replace('\n', '<br />\n'))
            html_body.set_type('text/html')
            email_message_alternative.attach(html_body)

            email_message.attach(email_message_alternative)

        aws_account_name = notification.content['aws_account_name']
        aws_access_key = notification.content['aws_access_key']
        aws_secret_key = notification.content['aws_secret_key']
        aws_region = notification.content['aws_region']
        email_from = notification.content['email_from']

        email_message['Subject'] = subject
        email_message['From'] = email_from
        email_message['To'] = ','.join(targets)
        email_message['Date'] = formatdate(None, True)

        conn = boto.ses.connect_to_region(
            aws_region,
            aws_access_key_id = aws_access_key,
            aws_secret_access_key = aws_secret_key
        )

        conn.send_email(
            email_message['From'],
            email_message['Subject'],
            email_message,
            email_message['To'],
            format = notification.content['body_content_type']
        )

        log.debug("Notification '%s' sent emails to: %s",
                     notification.id, targets)

    def getActionableTargets(self, target):
        """
        @param target: This is an object that implements the IProvidesEmailAddresses
            interface.
        @type target: UserSettings or GroupSettings.
        """
        if IProvidesEmailAddresses.providedBy(target):
            return target.getEmailAddresses()

    def _stripTags(self, data):
        """A quick html => plaintext converter
           that retains and displays anchor hrefs

           stolen from the old zenactions.
           @todo: needs to be updated for the new data structure?
        """
        tags = re.compile(r'<(.|\n)+?>', re.I | re.M)
        aattrs = re.compile(r'<a(.|\n)+?href=["\']([^"\']*)[^>]*?>([^<>]*?)</a>', re.I | re.M)
        anchors = re.finditer(aattrs, data)
        for x in anchors: data = data.replace(x.group(), "%s: %s" % (x.groups()[2], x.groups()[1]))
        data = re.sub(tags, '', data)
        return data

    def updateContent(self, content=None, data=None):
        updates = dict()
        updates['body_content_type'] = data.get('body_content_type', 'html')

        properties = ['subject_format', 'body_format', 'clear_subject_format', 'clear_body_format']
        properties.extend(['aws_account_name', 'aws_access_key', 'aws_secret_key', 'aws_region', 'email_from'])
        for k in properties:
            updates[k] = data.get(k)

        content.update(updates)
