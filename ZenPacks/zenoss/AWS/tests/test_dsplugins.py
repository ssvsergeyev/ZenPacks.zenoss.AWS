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

class TestPlugins(BaseTestCase):
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



def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPlugins))
    return suite
