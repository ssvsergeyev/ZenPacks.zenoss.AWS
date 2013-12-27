##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from Products.ZenTestCase.BaseTestCase import BaseTestCase

from mock import Mock, patch, MagicMock

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

class TestAWSBasePlugin(BaseTestCase):
    def asterSetUp(self):
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

        res = self.plugin.onSuccess(result, sentilen.any_value)

        self.assertEquals(len(result['events']), 2)
        self.assertEquals(result['events'][0]['severity'], 0)
        self.assertEquals(result['events'][1]['eventClass'], '/Status')



def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestReservedInstancesPlugins))
    return suite
