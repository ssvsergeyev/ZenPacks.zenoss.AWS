##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from mock import Mock, patch, sentinel

from Products.ZenTestCase.BaseTestCase import BaseTestCase
# from Products.ZenCollector.services.config import DeviceProxy

from ZenPacks.zenoss.AWS.modeler.plugins.aws import EC2


class TestAWSCollector(BaseTestCase):

    def test_tags_string(self):
        tags = {u'tag': u'test', u'tag1': u'test1'}
        self.assertEquals(EC2.tags_string(tags), 'tag: test, tag1: test1;')

    def test_check_tag(self):
        tags = {u'tag': u'test'}
        tags1 = {u'tag': u'test2'}
        value = 'tag: test; tag1: test1; '
        self.assertEquals(EC2.check_tag(value, tags), True)
        self.assertEquals(EC2.check_tag(value, tags1), False)

    def test_path_to_pem(self):
        values = ['{"region_name":"test","pem_path":"path"}']
        self.assertEquals(EC2.path_to_pem('test', values), 'path')
        self.assertEquals(EC2.path_to_pem('test1', values), '')

    def test_vpn_gateways_rm(self):
        gateway = Mock()
        gateway.tags = [sentinel.name, ]
        gateways = [gateway, ]
        gateway.state = sentinel.state
        self.assertEquals(
            EC2.vpn_gateways_rm('test', gateways).__dict__['maps'][0].state,
            sentinel.state
        )

    def test_vpn_queues_rm(self):
        q = Mock()
        q.name = sentinel.name
        qs = [q, ]
        self.assertEquals(
            EC2.vpn_queues_rm('test', qs).__dict__['maps'][0].title,
            sentinel.name
        )


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAWSCollector))
    return suite
