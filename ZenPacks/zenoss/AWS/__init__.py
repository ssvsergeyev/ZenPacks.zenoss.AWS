##############################################################################
#
# Copyright (C) Zenoss, Inc. 2012, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os
import json

from Products.ZenModel.ZenPack import ZenPackBase

from collections import defaultdict


# Modules containing model classes. Used by zenchkschema to validate
# bidirectional integrity of defined relationships.
productNames = (
    'EC2Account',
    'EC2Instance',
    'EC2Region',
    'EC2Volume',
    'EC2VPC',
    'EC2VPCSubnet',
    'EC2Zone',
    'EC2Reservation',
    'EC2ElasticIP',
    'EC2Image',
    'S3Bucket',
)

# Useful to avoid making literal string references to module and class names
# throughout the rest of the ZenPack.
MODULE_NAME = {}
CLASS_NAME = {}
for product_name in productNames:
    ZP_NAME = 'ZenPacks.zenoss.AWS'
    MODULE_NAME[product_name] = '.'.join([ZP_NAME, product_name])
    CLASS_NAME[product_name] = '.'.join([ZP_NAME, product_name, product_name])

EC2INSTANCE_TYPES = defaultdict(lambda: '')
try:
    json_data = open(os.path.join(os.path.dirname(__file__), 'aws.json'))
    data = json.load(json_data)
    all_types = data['services']['Elastic Compute Cloud']['instance_types']
    EC2INSTANCE_TYPES = {}
    for i_type in all_types:
        EC2INSTANCE_TYPES[i_type] = '; '.join(
            ['%s: %s' % (k, v) for (k, v) in all_types[i_type].items()]
        )
except:
    pass


class ZenPack(ZenPackBase):
    '''
    ZenPack loader.
    '''
    pass
