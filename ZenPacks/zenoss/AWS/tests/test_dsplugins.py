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
        self.assertEquals(
            result['events'][0]['severity'],
            ZenEventClasses.Clear
        )
        self.assertEquals(result['events'][1]['eventClass'], '/Status')

    @patch('ZenPacks.zenoss.AWS.dsplugins.log')
    def test_onError(self, log):
        error = Mock()
        error.type = "test"
        e = self.plugin.onError(error, sentinel.anything)

        self.assertEquals(len(e['events']), 1)
        self.assertEquals(e['events'][0]['severity'], ZenEventClasses.Error)

    @patch('ZenPacks.zenoss.AWS.dsplugins.log')
    def test_onErrorMessage(self, log):
        config = Mock()
        ds = Mock()
        config.datasources = [ds]
        self.plugin.component = 'world'

        e = self.plugin.onError('<Message>Hello</Message> world', config)

        self.assertEquals(len(e['events']), 1)
        e = e['events'][0]
        self.assertEquals(e['severity'], ZenEventClasses.Info)


class TestS3BucketPlugin(BaseTestCase):

    @patch('ZenPacks.zenoss.AWS.dsplugins.S3Connection')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_collect(self, defer, S3Connection):
        key = Mock()
        key.size = 3

        bucket = Mock()
        bucket.get_all_keys.return_value = [key] * 2
        bucket.name = sentinel.component

        S3Connection.return_value\
            .get_all_buckets.return_value = [bucket]

        defer.maybeDeferred = lambda x: x()

        config = Mock()
        config.datasources = [MagicMock()]
        config.datasources[0].component = sentinel.component

        from ZenPacks.zenoss.AWS.dsplugins import S3BucketPlugin
        plugin = S3BucketPlugin()
        data = plugin.inner(config)

        self.assertIn(sentinel.component, data['values'])
        d = data['values'][sentinel.component]
        self.assertEquals(d['keys_count'][0], 2)
        self.assertEquals(d['total_size'][0], 6)


class TestReservedInstancesPlugins(BaseTestCase):
    @patch('ZenPacks.zenoss.AWS.dsplugins.unreserved_instance_count')
    @patch('ZenPacks.zenoss.AWS.dsplugins.boto')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_unreserved_instances_plugin(
        self, defer, boto, unreserved_instance_count
    ):
        unreserved_instance_count.return_value = 1
        defer.maybeDeferred = lambda x: x()
        config = Mock()
        config.datasources = [MagicMock()]

        from ZenPacks.zenoss.AWS.dsplugins import EC2UnreservedInstancesPlugin
        plugin = EC2UnreservedInstancesPlugin()
        data = plugin.inner(config)

        self.assertEquals(data['events'][0]['eventClass'], '/AWS/Suggestion')
        self.assertEquals(data['events'][0]['severity'], ZenEventClasses.Info)

    @patch('ZenPacks.zenoss.AWS.dsplugins.unused_reserved_instances_count')
    @patch('ZenPacks.zenoss.AWS.dsplugins.boto')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_unused_reserved_instance_plugin(
        self, defer, boto, unused_reserved_instances_count
    ):
        unused_reserved_instances_count.return_value = 1
        defer.maybeDeferred = lambda x: x()
        config = Mock()
        config.datasources = [MagicMock()]
        from ZenPacks.zenoss.AWS.dsplugins import EC2UnusedReservedInstancesPlugin

        plugin = EC2UnusedReservedInstancesPlugin()
        data = plugin.inner(config)

        self.assertEquals(data['events'][0]['eventClass'], '/AWS/Suggestion')
        self.assertEquals(data['events'][0]['severity'], ZenEventClasses.Info)


class TestEC2BaseStatePlugin(BaseTestCase):

    @patch('ZenPacks.zenoss.AWS.dsplugins.boto')
    @patch('ZenPacks.zenoss.AWS.dsplugins.defer')
    def test_collect(self, defer, boto):
        defer.maybeDeferred = lambda x: x()

        config = Mock()
        config.datasources = [MagicMock()]
        config.datasources[0].component = sentinel.component

        from ZenPacks.zenoss.AWS.dsplugins import EC2BaseStatePlugin
        plugin = EC2BaseStatePlugin()
        plugin.results_to_maps = lambda *args: sentinel.map
        data = plugin.inner(config)

        self.assertEquals(len(data['maps']), 1)
        self.assertEquals(data['maps'][0], sentinel.map)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAWSBasePlugin))
    suite.addTest(makeSuite(TestS3BucketPlugin))
    suite.addTest(makeSuite(TestReservedInstancesPlugins))
    suite.addTest(makeSuite(TestEC2BaseStatePlugin))
    return suite
