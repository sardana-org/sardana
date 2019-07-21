# This serves to upgrade MacroServer environment from Python 2 to Python 3:

# IMPORTANT: IT HAS TO BE USED WITH PYTHON 2!!!

# Usage: python upgrade_env.py <ms_dev_name|ms_dev_alias>

# From: https://stackoverflow.com/questions/27493733/use-python-2-shelf-in-python-3  # noqa
# Thanks to Eric Myers

import os
import sys
import shelve
import dumbdbm

import PyTango


DefaultEnvBaseDir = "/tmp/tango"
DefaultEnvRelDir = "%(ds_exec_name)s/%(ds_inst_name)s/macroserver.properties"


def get_ms_properties(ms_name, ms_ds_name):
    db = PyTango.Database()
    prop = db.get_device_property(ms_name, "EnvironmentDb")
    ms_properties = prop["EnvironmentDb"]
    if not ms_properties:
        dft_ms_properties = os.path.join(
            DefaultEnvBaseDir,
            DefaultEnvRelDir)
        ds_inst_name = ms_ds_name.split("/")[1]
        ms_properties = dft_ms_properties % {
            "ds_exec_name": "MacroServer",
            "ds_inst_name": ds_inst_name}
    ms_properties = os.path.normpath(ms_properties)
    return ms_properties


def dumbdbm_shelve(filename, flag="c"):
    return shelve.Shelf(dumbdbm.open(filename, flag))


def upgrade_env(ms_name):
    db = PyTango.Database()
    ms_info = db.get_device_info(ms_name)
    ms_ds_name = ms_info.ds_full_name

    env_filename = get_ms_properties(ms_name, ms_ds_name)
    env_filename_py2 = env_filename + ".py2"

    os.rename(env_filename, env_filename_py2)

    out_shelf = dumbdbm_shelve(env_filename)
    in_shelf = shelve.open(env_filename_py2)

    key_list = in_shelf.keys()
    for key in key_list:
        out_shelf[key] = in_shelf[key]

    out_shelf.close()
    in_shelf.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "python upgrade_env.py <ms_dev_name|ms_dev_alias>"  # noqa
        sys.exit(1)
    ms_name = sys.argv[1]
    upgrade_env(ms_name)
