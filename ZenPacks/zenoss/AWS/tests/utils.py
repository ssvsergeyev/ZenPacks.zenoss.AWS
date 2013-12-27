##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import transaction

from zope.event import notify

from Products.ZenUtils.Utils import monkeypatch
from Products.Zuul.catalog.events import IndexingEvent


def add_obj(relationship, obj):
    '''
    Add obj to relationship, index it, then returns the persistent
    object.
    '''
    relationship._setObject(obj.id, obj)
    obj = relationship._getOb(obj.id)
    obj.index_object()
    notify(IndexingEvent(obj))
    return obj


@monkeypatch('Products.Zuul')
def get_dmd():
    """
    Retrieve the DMD object. Handle unit test connection oddities.

    This has to be monkeypatched on Products.Zuul instead of
    Products.Zuul.utils because it's already imported into Products.Zuul
    by the time this monkeypatch happens.
    """
    try:
        # original is injected by the monkeypatch decorator.
        return original()

    except AttributeError:
        connections = transaction.get()._synchronizers.data.values()[:]
        for cxn in connections:
            app = cxn.root()['Application']
            if hasattr(app, 'zport'):
                return app.zport.dmd


def test_account(dmd, factor=1):
    '''
    Return an example EC2Account with a full set of example components.
    '''
    from ZenPacks.zenoss.AWS.EC2Region import EC2Region
    from ZenPacks.zenoss.AWS.EC2Zone import EC2Zone
    from ZenPacks.zenoss.AWS.EC2VPC import EC2VPC
    from ZenPacks.zenoss.AWS.EC2VPCSubnet import EC2VPCSubnet
    from ZenPacks.zenoss.AWS.EC2Instance import EC2Instance
    from ZenPacks.zenoss.AWS.EC2Volume import EC2Volume
    from ZenPacks.zenoss.AWS.S3Bucket import S3Bucket
    from ZenPacks.zenoss.AWS.EC2ElasticIP import EC2ElasticIP
    from ZenPacks.zenoss.AWS.EC2Image import EC2Image
    from ZenPacks.zenoss.AWS.VPNGateway import VPNGateway
    from ZenPacks.zenoss.AWS.SQSQueue import SQSQueue

    dc = dmd.Devices.createOrganizer('/AWS/EC2')
    dc.setZenProperty('zPythonClass', 'ZenPacks.zenoss.AWS.EC2Account')

    account = dc.createInstance('account')
    account.setPerformanceMonitor('localhost')
    account.linuxDeviceClass = '/Server/Linux'
    account.index_object()
    notify(IndexingEvent(account))

    # Regions
    for region_id in range(factor):
        region = add_obj(
            account.regions,
            EC2Region('region%s' % (
                region_id)))

        # Zones
        for zone_id in range(factor):
            zone = add_obj(
                region.zones,
                EC2Zone('zone%s-%s' % (
                    region_id, zone_id)))

        # Images
        for image_id in range(factor):
            image = add_obj(
                region.images,
                EC2Image('image%s-%s' % (
                    region_id, image_id)))

            # VPCs
            for vpc_id in range(factor):
                vpc = add_obj(
                    region.vpcs,
                    EC2VPC('vpc%s-%s-%s' % (
                        region_id, zone_id, vpc_id)))

                # VPC Subnets
                for subnet_id in range(factor):
                    subnet = add_obj(
                        region.vpc_subnets,
                        EC2VPCSubnet('subnet%s-%s-%s-%s' % (
                            region_id, zone_id, vpc_id, subnet_id)))

                    subnet.setZoneId(zone.id)
                    subnet.setVPCId(vpc.id)

                    # Instances
                    for instance_id in range(factor):
                        instance = add_obj(
                            region.instances,
                            EC2Instance('instance%s-%s-%s-%s-%s' % (
                                region_id, zone_id, vpc_id, subnet_id,
                                instance_id)))

                        instance.setZoneId(zone.id)
                        instance.setImageId(image.id)
                        instance.setVPCSubnetId(subnet.id)
                        instance.private_ip_address = '10.77.77.77'
                        instance.create_guest()

                        # Volumes
                        for volume_id in range(factor):
                            volume = add_obj(
                                region.volumes,
                                EC2Volume('volume%s-%s-%s-%s-%s-%s' % (
                                    region_id, zone_id, vpc_id, subnet_id,
                                    instance_id, volume_id)))

                            volume.setZoneId(zone.id)
                            volume.setInstanceId(instance.id)

        # Elastic IPs
        for elastic_ip_id in range(factor):
            elastic_ip = add_obj(
                region.elastic_ips,
                EC2ElasticIP('elastic_ip%s-%s' % (
                    region_id, elastic_ip_id)))

        # SQS Queue
        for queue_id in range(factor):
            queue = add_obj(
                region.queues,
                SQSQueue('queue%s-%s' % (
                    region_id, queue_id)))

        # VPNGateways
        for vpn_gateway_id in range(factor):
            vpn_gateway = add_obj(
                region.vpn_gateways,
                VPNGateway('vpn_gateway%s-%s' % (
                    region_id, vpn_gateway_id)))

    # S3Buckets
    for bucket_id in range(factor):
        bucket = add_obj(
            account.s3buckets,
            S3Bucket('s3bucket%s' % (
                bucket_id)))

    return account
