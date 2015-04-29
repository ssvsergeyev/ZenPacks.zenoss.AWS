##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

'''
Collects information about AWS S3 buckets.
'''

import collections
import json

from itertools import chain
from logging import getLogger
log = getLogger('zen.ZenModeler')

from socket import gaierror

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap

from Products.ZenUtils.Utils import prepId

from ZenPacks.zenoss.AWS import MODULE_NAME
from ZenPacks.zenoss.AWS.utils import addLocalLibPath, format_time

addLocalLibPath()

from boto.ec2.connection import EC2ResponseError
from boto.s3.connection import S3Connection
import boto

'''
Models S3 Buckets for an Amazon EC2 account.
'''


class S3Buckets(PythonPlugin):
    deviceProperties = PythonPlugin.deviceProperties + (
        'ec2accesskey',
        'ec2secretkey',
    )

    def collect(self, device, log):
        return True

    def process(self, device, results, log):
        log.info(
            'Modeler %s processing data for device %s',
            self.name(), device.id)

        accesskey = getattr(device, 'ec2accesskey', None)
        secretkey = getattr(device, 'ec2secretkey', None)

        old_logger = boto.log.error
        boto.log.error = lambda x: x
        try:
            if not secretkey or not accesskey:
                raise EC2ResponseError('', '', '')
            s3connection = S3Connection(accesskey, secretkey)
        except EC2ResponseError:
            log.error('Invalid Keys. '
                      'Check your EC2 Access Key and EC2 Secret Key.')
            return
        except gaierror, e:
            log.error(e.strerror)
            return
        finally:
            boto.log.error = old_logger

        maps = collections.OrderedDict([
            ('s3buckets', []),
        ])

        # S3Buckets
        maps['s3buckets'].append(
            s3buckets_rm(s3connection.get_all_buckets())
        )

        return list(chain.from_iterable(maps.itervalues()))


def s3buckets_rm(buckets):
    '''
    Return buckets RelationshipMap given a BucketInfo
    ResultSet.
    '''
    bucket_oms = []
    for bucket in buckets:
        bucket_oms.append(ObjectMap(data={
            'id': prepId(bucket.name),
            'title': bucket.name,
            'creation_date': format_time(bucket.creation_date),
        }))

    return RelationshipMap(
        relname='s3buckets',
        modname=MODULE_NAME['S3Bucket'],
        objmaps=bucket_oms
    )
