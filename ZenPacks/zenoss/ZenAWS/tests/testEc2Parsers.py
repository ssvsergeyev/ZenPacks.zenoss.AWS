##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


import os

from Products.ZenRRD.tests.BaseParsersTestCase import BaseParsersTestCase

from ZenPacks.zenoss.ZenAWS.parsers.ec2.instances import instances
from ZenPacks.zenoss.ZenAWS.parsers.ec2.manager import manager


class Ec2ParsersTestCase(BaseParsersTestCase):

    def testEc2Parsers(self):
        """
        Test all of the parsers that have test data files in the data
        directory.
        """

        parserMap = {
            'instances': instances,
            'list instances': instances,
            'manager': manager
                     }

        datadir = "%s/parserdata/ec2" % (
                        os.path.dirname(__file__))

        self._testParsers(datadir, parserMap)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(Ec2ParsersTestCase))
    return suite
