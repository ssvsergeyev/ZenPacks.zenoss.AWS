##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ZenPacks.zenoss.AWS.datasources.SQSDataSource import SQSDataSourcePlugin

class TestSQS(BaseTestCase):
    def test_process(self):
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSQS))
    return suite
