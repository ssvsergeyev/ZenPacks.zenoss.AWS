##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from mock import Mock, sentinel

from Products.ZenTestCase.BaseTestCase import BaseTestCase
# from Products.ZenCollector.services.config import DeviceProxy

from ZenPacks.zenoss.AWS.modeler.plugins.aws import EC2


class TestAWSCollector(BaseTestCase):

    def afterSetUp(self):
        self.test = Mock()
        self.test.id = sentinel.id
        self.test.name = sentinel.name
        self.test.tags = [sentinel.name, ]
        self.test.state = sentinel.state
        self.test.public_ip = sentinel.public_ip
        self.test.block_device_mapping = {}
        self.tests = [self.test, ]

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

    def test_block_device(self):
        block_device = Mock()
        block_device_properties = (
            'ephemeral_name',
            'snapshot_id',
            'size',
            'delete_on_termination',
            'volume_type'
        )
        for prop in block_device_properties:
            setattr(block_device, prop, 'test')
        values = {"test": block_device}
        result = "test=test:test:test:test:test"
        self.assertEquals(EC2.block_device(values), result)
        self.assertEquals(EC2.block_device(None), '')

    def test_vpn_gateways_rm(self):
        self.assertEquals(
            EC2.vpn_gateways_rm('test', self.tests).__dict__['maps'][0].state,
            sentinel.state
        )

    def test_vpn_queues_rm(self):
        self.assertEquals(
            EC2.vpn_queues_rm('test', self.tests).__dict__['maps'][0].title,
            sentinel.name
        )

    def test_images_rm(self):
        self.assertEquals(
            EC2.images_rm('test', self.tests).__dict__['maps'][0].title,
            sentinel.name
        )

    def test_elastic_ips_rm(self):
        self.assertEquals(
            EC2.elastic_ips_rm('test', self.tests).__dict__['maps'][0].title,
            sentinel.public_ip
        )

    def test_reserved_instances_rm(self):
        self.assertEquals(
            EC2.reserved_instances_rm('test', self.tests).__dict__['maps'][0].title,
            sentinel.id
        )

    def test_s3buckets_rm(self):
        self.tests[0].creation_date = 'DDTHH.asdf'
        map = EC2.s3buckets_rm(self.tests).__dict__['maps'][0]

        self.assertEquals(map.title, sentinel.name)
        self.assertEquals(map.creation_date, 'DD HH')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAWSCollector))
    return suite
