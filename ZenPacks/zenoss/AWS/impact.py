##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from Products.ZenRelations.ToManyRelationship import ToManyRelationshipBase
from Products.ZenRelations.ToOneRelationship import ToOneRelationship
from Products.ZenUtils.guid.interfaces import IGlobalIdentifier

from ZenPacks.zenoss.Impact.impactd.relations import ImpactEdge

from ZenPacks.zenoss.AWS.EC2Instance import ec2_instance_for_device


RP = 'ZenPacks.zenoss.AWS'
AVAILABILITY = 'AVAILABILITY'
PERCENT = 'policyPercentageTrigger'
THRESHOLD = 'policyThresholdTrigger'


def guid(obj):
    return IGlobalIdentifier(obj).getGUID()


def edge(source, target):
    return ImpactEdge(source, target, RP)


class BaseRelationsProvider(object):
    relationship_provider = RP

    impact_relationships = None
    impacted_by_relationships = None

    def __init__(self, adapted):
        self._object = adapted

    def belongsInImpactGraph(self):
        return True

    def guid(self):
        if not hasattr(self, '_guid'):
            self._guid = guid(self._object)

        return self._guid

    def impact(self, relname):
        relationship = getattr(self._object, relname, None)
        if relationship:
            if isinstance(relationship, ToOneRelationship):
                obj = relationship()
                if obj:
                    yield edge(self.guid(), guid(obj))

            elif isinstance(relationship, ToManyRelationshipBase):
                for obj in relationship():
                    yield edge(self.guid(), guid(obj))

    def impacted_by(self, relname):
        relationship = getattr(self._object, relname, None)
        if relationship:
            if isinstance(relationship, ToOneRelationship):
                obj = relationship()
                if obj:
                    yield edge(guid(obj), self.guid())

            elif isinstance(relationship, ToManyRelationshipBase):
                for obj in relationship():
                    yield edge(guid(obj), self.guid())

    def getEdges(self):
        if self.impact_relationships is not None:
            for impact_relationship in self.impact_relationships:
                for impact in self.impact(impact_relationship):
                    yield impact

        if self.impacted_by_relationships is not None:
            for impacted_by_relationship in self.impacted_by_relationships:
                for impacted_by in self.impacted_by(impacted_by_relationship):
                    yield impacted_by


class EC2AccountRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['regions', 's3buckets']


class EC2RegionRelationsProvider(BaseRelationsProvider):
    impacted_by_relationships = ['account']
    impact_relationships = ['zones', 'vpcs', 'elastic_ips', 'reservations',
                            'vpn_gateways', 'queues', 'images']


class EC2ZoneRelationsProvider(BaseRelationsProvider):
    impacted_by_relationships = ['region']
    impact_relationships = ['vpc_subnets', 'instances', 'volumes']


class EC2VPCRelationsProvider(BaseRelationsProvider):
    impacted_by_relationships = ['region']
    impact_relationships = ['vpc_subnets']


class EC2VPCSubnetRelationsProvider(BaseRelationsProvider):
    impacted_by_relationships = ['vpc', 'zone']
    impact_relationships = ['instances']

# todo: test on zenoss resource manager 4.2.4
class EC2ReservationRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['region']


class EC2ElasticIPRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['region']


class EC2ImageRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['region']
    impacted_by_relationships = ['instances']


class S3BucketRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['account']


class VPNGatewayRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['region']


class SQSQueueRelationsProvider(BaseRelationsProvider):
    impact_relationships = ['region']


class EC2InstanceRelationsProvider(BaseRelationsProvider):
    impacted_by_relationships = ['vpc_subnet', 'zone', 'volumes', 'images']

    def getEdges(self):
        for impact in super(EC2InstanceRelationsProvider, self).getEdges():
            yield impact

        guest = self._object.guest_device()
        if guest:
            yield edge(self.guid(), guid(guest))


class EC2VolumeRelationsProvider(BaseRelationsProvider):
    impacted_by_relationships = ['zone']
    impact_relationships = ['instance']


class DeviceRelationsProvider(BaseRelationsProvider):
    def getEdges(self):
        instance = ec2_instance_for_device(self._object)
        if instance:
            yield edge(guid(instance), self.guid())
