##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

'''
AWS custom device loaders.
'''

from zope.interface import implements

from Products.Zuul import getFacade
from Products.ZenModel.interfaces import IDeviceLoader


class EC2AccountLoader(object):
    '''
    EC2 account loader.

    Used by including lines such as the following in a zenbatchload
    input file::

        /Devices/AWS/EC2 loader='ec2account', loader_arg_keys=['accountname', 'accesskey', 'secretkey', 'collector']
        my-aws-account accountname='my-aws-account', accesskey='<accesskey>', secretkey='<secretkey>', collector='localhost'
    '''

    implements(IDeviceLoader)

    def load_device(
            self, dmd, accountname, accesskey, secretkey,
            collector='localhost'):

        return getFacade('aws', dmd).add_ec2account(
            accountname, accesskey, secretkey, collector)
