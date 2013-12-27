##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from Products.ZenEvents import ZenEventClasses
from Products.ZenTestCase.BaseTestCase import BaseTestCase

from mock import Mock, patch, MagicMock, sentinel

class TestAWSBasePlugin(BaseTestCase):
    def afterSetUp(self):
        from ZenPacks.zenoss.AWS.dsplugins import AWSBasePlugin
        self.plugin = AWSBasePlugin()

    def test_params_empty(self):
        ds = Mock()
        # method will rise TypeError when called with two args
        ds.talesEval = lambda x: None

        self.assertEquals(self.plugin.params(ds, Mock()), {})

    def test_params_region(self):
        ds = Mock()
        ds.talesEval = lambda x, y: sentinel.region

        self.assertEquals(
            self.plugin.params(ds, Mock()),
            {'region': sentinel.region}
        )

    def test_onSuccess(self):
        result = self.plugin.new_data()
        result['values'] = {'c1': 1, 'c2': 2}
        result['events'] = []

        res = self.plugin.onSuccess(result, sentinel.any_value)

        self.assertEquals(len(result['events']), 2)
        self.assertEquals(result['events'][0]['severity'], ZenEventClasses.Clear)
        self.assertEquals(result['events'][1]['eventClass'], '/Status')


    @patch('ZenPacks.zenoss.AWS.dsplugins.log')
    def test_onError(self, log):
        e = self.plugin.onError(sentinel.error, sentinel.anything)

        self.assertEquals(len(e['events']), 1)
        self.assertEquals(e['events'][0]['severity'], ZenEventClasses.Error)
        log.error.assert_called_with(sentinel.error)
        

class TestS3BucketPlugin(BaseTestCase):

    @patch('ZenPacks.zenoss.AWS.dsplugins.S3Connection')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_collect(self, defer, S3Connection):
        key = Mock()
        key.size = 3
        S3Connection.return_value.get_bucket.return_value.get_all_keys.return_value = [key] * 2

        defer.maybeDeferred = lambda x: x()

        config = Mock()
        config.datasources = [MagicMock()]
        config.datasources[0].component = sentinel.component

        from ZenPacks.zenoss.AWS.dsplugins import S3BucketPlugin
        plugin = S3BucketPlugin()
        data = plugin.collect(config)

        self.assertIn(sentinel.component, data['values'])
        d = data['values'][sentinel.component]
        self.assertEquals(d['keys_count'][0], 2)
        self.assertEquals(d['total_size'][0], 6)


class TestReservedInstancesPlugins(BaseTestCase):
    @patch('ZenPacks.zenoss.AWS.dsplugins.unreserved_instance_count')
    @patch('ZenPacks.zenoss.AWS.dsplugins.boto')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_unreserved_instances_plugin(self, defer, boto, unreserved_instance_count):
        unreserved_instance_count.return_value = 1
        defer.maybeDeferred = lambda x: x()
        config = Mock()
        config.datasources = [MagicMock()]

        from ZenPacks.zenoss.AWS.dsplugins import EC2UnreservedInstancesPlugin
        plugin = EC2UnreservedInstancesPlugin()
        data = plugin.collect(config)

        self.assertEquals(data['events'][0]['eventClass'], '/AWS/Suggestion')
        self.assertEquals(data['events'][0]['severity'], ZenEventClasses.Info)

    @patch('ZenPacks.zenoss.AWS.dsplugins.unused_reserved_instances_count')
    @patch('ZenPacks.zenoss.AWS.dsplugins.boto')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_unused_reserved_instance_plugin(self, defer, boto, unused_reserved_instances_count):
        unused_reserved_instances_count.return_value = 1
        defer.maybeDeferred = lambda x: x()
        config = Mock()
        config.datasources = [MagicMock()]
        from ZenPacks.zenoss.AWS.dsplugins import EC2UnusedReservedInstancesPlugin

        plugin = EC2UnusedReservedInstancesPlugin()
        data = plugin.collect(config)

        self.assertEquals(data['events'][0]['eventClass'], '/AWS/Suggestion')
        self.assertEquals(data['events'][0]['severity'], ZenEventClasses.Info)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAWSBasePlugin))
    suite.addTest(makeSuite(TestS3BucketPlugin))
    suite.addTest(makeSuite(TestReservedInstancesPlugins))
    return suite
