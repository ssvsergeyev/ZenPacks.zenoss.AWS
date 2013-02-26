###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013 Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

from twisted.internet.error import ConnectionRefusedError, TimeoutError


def addLocalLibPath():
    """
    Helper to add the ZenPack's lib directory to PYTHONPATH.
    """
    import os
    import site

    site.addsitedir(os.path.join(os.path.dirname(__file__), 'lib'))


def result_errmsg(result):
    """Return a useful error message string given a twisted errBack result."""
    try:
        from pywbem.cim_operations import CIMError

        if result.type == ConnectionRefusedError:
            return 'connection refused. Check IP and zWBEMPort'
        elif result.type == TimeoutError:
            return 'connection timeout. Check IP and zWBEMPort'
        elif result.type == CIMError:
            if '401' in result.value.args[1]:
                return 'login failed. Check zWBEMUsername and zWBEMPassword'
            else:
                return result.value.args[1]
        else:
            return result.getErrorMessage()
    except AttributeError:
        pass

    return str(result)
