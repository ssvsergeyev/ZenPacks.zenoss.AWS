##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import functools

from zope.component import subscribers

from Products.Five import zcml

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from Products.ZenUtils.guid.interfaces import IGUIDManager
from Products.ZenUtils.Utils import unused

from ZenPacks.zenoss.AWS.tests.utils import test_account


def require_impact(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            import ZenPacks.zenoss.Impact
            unused(ZenPacks.zenoss.Impact)
        except ImportError:
            return

        return f(*args, **kwargs)

    return wrapper


def impacts_for(thing):
    '''
    Return a two element tuple.

    First element is a list of object ids impacted by thing. Second element is
    a list of object ids impacting thing.
    '''
    try:
        from ZenPacks.zenoss.Impact.impactd.interfaces import \
            IRelationshipDataProvider

    except ImportError:
        return ([], [])

    impacted_by = []
    impacting = []

    guid_manager = IGUIDManager(thing.getDmd())
    for subscriber in subscribers([thing], IRelationshipDataProvider):
        for edge in subscriber.getEdges():
            source = guid_manager.getObject(edge.source)
            impacted = guid_manager.getObject(edge.impacted)
            if source == thing:
                impacted_by.append(impacted.id)
            elif impacted == thing:
                impacting.append(source.id)

    return (impacted_by, impacting)


def triggers_for(thing):
    '''
    Return a list of triggers for thing.
    '''
    try:
        from ZenPacks.zenoss.Impact.impactd.interfaces import INodeTriggers
    except ImportError:
        return []

    triggers = []

    for sub in subscribers((thing,), INodeTriggers):
        triggers.extend(sub.get_triggers())

    return triggers


class TestImpact(BaseTestCase):
    '''
    Test suite for all Impact adapters.
    '''

    def afterSetUp(self):
        super(TestImpact, self).afterSetUp()

        try:
            import ZenPacks.zenoss.DynamicView
            zcml.load_config('configure.zcml', ZenPacks.zenoss.DynamicView)
        except ImportError:
            pass

        try:
            import ZenPacks.zenoss.Impact
            zcml.load_config('meta.zcml', ZenPacks.zenoss.Impact)
            zcml.load_config('configure.zcml', ZenPacks.zenoss.Impact)
        except ImportError:
            pass

        import ZenPacks.zenoss.AWS
        zcml.load_config('configure.zcml', ZenPacks.zenoss.AWS)

    def account(self):
        if not hasattr(self, '_account'):
            self._account = test_account(self.dmd, factor=1)

        return self._account

    @require_impact
    def test_EC2AccountImpacts(self):
        account_impacts, account_impacted_by = impacts_for(self.account())

        # Account -> Region
        self.assertTrue('region0' in account_impacts)

    @require_impact
    def test_EC2RegionImpacts(self):
        region = self.account().getObjByPath(
            'regions/region0')

        region_impacts, region_impacted_by = impacts_for(region)

        # Account -> Region
        self.assertTrue('account' in region_impacted_by)

        # Region -> Zone
        self.assertTrue('zone0-0' in region_impacts)

        # Region -> VPC
        self.assertTrue('vpc0-0-0' in region_impacts)

        # Negative check to verify no other impacts exist.
        self.assertEqual(len(region_impacted_by), 1)
        self.assertEqual(len(region_impacts), 2)

    @require_impact
    def test_EC2ZoneImpacts(self):
        zone = self.account().getObjByPath(
            'regions/region0/zones/zone0-0')

        zone_impacts, zone_impacted_by = impacts_for(zone)

        # Region -> Zone
        self.assertTrue('region0' in zone_impacted_by)

        # Zone -> Subnet
        self.assertTrue('subnet0-0-0-0' in zone_impacts)

        # Zone -> Instance
        self.assertTrue('instance0-0-0-0-0' in zone_impacts)

        # Zone -> Volume
        self.assertTrue('volume0-0-0-0-0-0' in zone_impacts)

        # Negative check to verify no other impacts exist.
        self.assertEqual(len(zone_impacted_by), 1)
        self.assertEqual(len(zone_impacts), 3)

    @require_impact
    def test_EC2VPCImpacts(self):
        vpc = self.account().getObjByPath(
            'regions/region0/vpcs/vpc0-0-0')

        vpc_impacts, vpc_impacted_by = impacts_for(vpc)

        # Region -> VPC
        self.assertTrue('region0' in vpc_impacted_by)

        # VPC -> Subnet
        self.assertTrue('subnet0-0-0-0' in vpc_impacts)

        # Negative check to verify no other impacts exist.
        self.assertEqual(len(vpc_impacted_by), 1)
        self.assertEqual(len(vpc_impacts), 1)

    @require_impact
    def test_EC2VPCSubnetImpacts(self):
        subnet = self.account().getObjByPath(
            'regions/region0/vpc_subnets/subnet0-0-0-0')

        subnet_impacts, subnet_impacted_by = impacts_for(subnet)

        # VPC -> Subnet
        self.assertTrue('vpc0-0-0' in subnet_impacted_by)

        # Zone -> Subnet
        self.assertTrue('zone0-0' in subnet_impacted_by)

        # Subnet -> Instance
        self.assertTrue('instance0-0-0-0-0' in subnet_impacts)

        # Negative check to verify no other impacts exist.
        self.assertEqual(len(subnet_impacted_by), 2)
        self.assertEqual(len(subnet_impacts), 1)

    @require_impact
    def test_EC2InstanceImpacts(self):
        instance = self.account().getObjByPath(
            'regions/region0/instances/instance0-0-0-0-0')

        instance_impacts, instance_impacted_by = impacts_for(instance)

        # Zone -> Instance
        self.assertTrue('zone0-0' in instance_impacted_by)

        # Subnet -> Instance
        self.assertTrue('subnet0-0-0-0' in instance_impacted_by)

        # Volume -> Instance
        self.assertTrue('volume0-0-0-0-0-0' in instance_impacted_by)

        # Instance -> Device
        self.assertTrue(instance.guest_device().id in instance_impacts)

        # Negative check to verify no other impacts exist.
        self.assertEqual(len(instance_impacted_by), 3)
        self.assertEqual(len(instance_impacts), 1)

    @require_impact
    def test_EC2VolumeImpacts(self):
        volume = self.account().getObjByPath(
            'regions/region0/volumes/volume0-0-0-0-0-0')

        volume_impacts, volume_impacted_by = impacts_for(volume)

        # Zone -> Volume
        self.assertTrue('zone0-0' in volume_impacted_by)

        # Volume -> Instance
        self.assertTrue('instance0-0-0-0-0' in volume_impacts)

        # Negative check to verify no other impacts exist.
        self.assertEqual(len(volume_impacted_by), 1)
        self.assertEqual(len(volume_impacts), 1)

    @require_impact
    def test_DeviceImpacts(self):
        instance = self.account().getObjByPath(
            'regions/region0/instances/instance0-0-0-0-0')

        device = instance.guest_device()

        device_impacts, device_impacted_by = impacts_for(device)

        # Instance -> Device
        self.assertTrue('instance0-0-0-0-0' in device_impacted_by)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestImpact))
    return suite
