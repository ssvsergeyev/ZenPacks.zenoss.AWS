##############################################################################
#
# Copyright (C) Zenoss, Inc. 2012, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from Products.ZenModel.ZenPack import ZenPackBase


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
    )

# Useful to avoid making literal string references to module and class names
# throughout the rest of the ZenPack.
MODULE_NAME = {}
CLASS_NAME = {}
for product_name in productNames:
    ZP_NAME = 'ZenPacks.zenoss.AWS'
    MODULE_NAME[product_name] = '.'.join([ZP_NAME, product_name])
    CLASS_NAME[product_name] = '.'.join([ZP_NAME, product_name, product_name])


class ZenPack(ZenPackBase):
    '''
    ZenPack loader.
    '''
    pass
