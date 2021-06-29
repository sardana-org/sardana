""" This serves to upgrade MeasurementGroups from Sardana 2 to Sardana 3:

To get usage help: python3 upgrade_mntgrp.py --help
"""

import re
import sys
try:
    import argparse
except ImportError:
    from taurus.external import argparse
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import tango
import taurus
from sardana.taurus.core.tango.sardana import registerExtensions


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def replace_tango_db(tango_db_pqdn, tango_db_fqdn, s):
    # first step: pqdn -> fqdn
    new_s = re.sub(tango_db_pqdn, tango_db_fqdn, s)
    # second step: add missing scheme
    new_s = re.sub("(?<!tango://)" + tango_db_fqdn,
                        "tango://" + tango_db_fqdn,
                        new_s)
    return new_s


def change_tango_prop_list(dev, prop_name, old_tango_db, new_tango_db,
                           verbose):
    property_ = dev.get_property(prop_name)[prop_name]
    new_property = []
    for item in property_:
        new_item = replace_tango_db(old_tango_db, new_tango_db, item)
        new_property.append(new_item)
    if verbose and property_ != new_property:
        print("changing {0} {1}".format(dev.name(), prop_name))
    dev.put_property({prop_name: new_property})


def change_mntgrp(pool, tango_db_pqdn, tango_db_fqdn, verbose):
    hwinfo = pool.getHWObj().info()
    server = hwinfo.server_id

    db = tango.Database()
    dev_cls = db.get_device_class_list(server)

    for dev, cls in grouper(dev_cls, 2):
        if cls == "MeasurementGroup":
            config_attr = tango.AttributeProxy(dev + "/Configuration")
            try:
                config = config_attr.get_property("__value")["__value"][0]
            except:
                continue
            new_config = replace_tango_db(tango_db_pqdn, tango_db_fqdn, config)
            if verbose and config != new_config:
                print("changing {0} Configuration".format(dev))
            config_attr.put_property({"__value": new_config})
            mnt_grp = tango.DeviceProxy(dev)
            change_tango_prop_list(mnt_grp, "elements", tango_db_pqdn,
                                   tango_db_fqdn, verbose)


def main():
    parser = argparse.ArgumentParser(
        description="Change Tango DB in Sardana measurement group "
                    "configurations"
    )
    parser.add_argument("pool", type=str,
                        help="Pool device name")
    parser.add_argument("tango_db_pqdn", action="store", type=str,
                        help="old Tango database e.g. tbl09:10000")
    parser.add_argument("tango_db_fqdn", action="store", type=str,
                        help="new Tango database e.g. tbl09.cells.es:10000")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    registerExtensions()
    device = taurus.Device(args.pool)
    try:
        hwinfo = device.getHWObj().info()
    except tango.DevFailed:
        print("Pool {} is not exported. Hint: start the DS. Exiting...".format(
            args.pool))
        sys.exit(-1)
    dev_class = hwinfo.dev_class
    if dev_class == "Pool":
        change_mntgrp(device, args.tango_db_pqdn, args.tango_db_fqdn,
                      args.verbose)
    else:
        print("Invalid model, expected Pool. Exiting...")
        sys.exit(-1)
    print("IMPORTANT: now restart the {0} device server".format(dev_class))


if __name__ == "__main__":
    main()
