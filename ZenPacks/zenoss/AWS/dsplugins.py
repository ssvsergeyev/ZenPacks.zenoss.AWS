######################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

from logging import getLogger
log = getLogger('zen.python')

import time

from boto.s3.connection import S3Connection
from twisted.internet import defer

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin


class S3BucketPlugin(PythonDataSourcePlugin):
    """
    Subclass of PythonDataSourcePlugin to monitor AWS S3Buckets.
    """
    proxy_attributes = (
        'ec2accesskey', 'ec2secretkey',
    )

    @defer.inlineCallbacks
    def collect(self, config):
        data = {'events': [], 'values': {}, 'maps': []}
        for ds in config.datasources:
            s3connection = S3Connection(ds.ec2accesskey, ds.ec2secretkey)
            bucket = s3connection.get_bucket(ds.component)
            keys = yield bucket.get_all_keys()

            t = time.time()
            data['values'][ds.component] = dict(
                keys_count=(len(keys), t),
                total_size=(sum([key.size for key in keys]), t),
            )

        defer.returnValue(data)

    def onSuccess(self, result, config):
        for component in result["values"].keys():
            result['events'].insert(0, {
                'component': component,
                'summary': 'Monitoring ok',
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': 0,
            })
        return result

    def onError(self, result, config):
        log.error(result)
        return {
            'vaues': {},
            'events': [{
                'summary': 'error: %s' % result,
                'eventClass': '/Status',
                'eventKey': 'aws_result',
                'severity': 4,
            }],
            'maps': [],
        }