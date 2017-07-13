# Sardana Configuration Tools

The configuration tools present in this directory are just a proof-of-concept
developed long time ago. Their maintenance was limited to very minimum in the
recent years. Furthermore some of them have never reached a functional state.
So please **use them on your own risk**.

The basic data format used by these tools are the FODS
(OpenDocument Flat XML Spreadsheet) files that can be manipulated with the
OpenOffice/LibreOffice application. Each FODS configuration file represents a
Sardana system, that may be composed from single or multiple Pool
and/or MacroServer instances. The `template.fods` file may serve to create a
Sardana system from scratch, or an existing Sardana system can be dumped to
this file.

## Exporting an existing Sardana system to a FODS file

This process consists of two parts:

1. Automated extraction of the Pool's configuration to an intermediate CSV file.
2. Manual filling of this configuration and additional configuration into the
   FODS file.

Prior to starting this process ensure that the Pool that you would like dump to
the file is running.

1. Dump the Pool's configuration to a CSV file using the `get_pool_config.py`
   script:

   `python get_pool_config.py <pool-device-name> > <path-to-csv-file>`

   e.g.

   `python get_pool_config.py pool/blxx/1 > pool_blxx_1.csv`

2. Open the CSV file with one of the spreadsheet application and use the "Tab"
   as column separator.

3. Open the FODS template and fill the necessary information:

   * *code* and *name* field in the *Global* sheet that will correspond to the
     family field in the Tango device name of the Pool and MacroServer e.g.
     blxx for pool/blxx/1 and macroserver/blxx/1 names
   * *Host* column in the *Servers* sheet that indicates the Tango Database host
     and port e.g. mypc:10000
   * *Path* fields in the *Servers* sheet that will correspond to the PoolPath
     and MacroPath properties of the Pool and MacroServer devices correspondingly

4. Copy and Paste the information about the Pool's elements from the CSV file
   into the FODS file. The *#* separator lines are useful to distinguish the
   elements' groups e.g.

### Known limitations

* MeasurementGroup configurations are not dumped
* Attribute parameters of the same element can not contain the same values
  e.g. *Min value* or *Min alarm* can not have values 10 and 10.

## Creating a Sardana system from a FODS file

Once the FODS file contains all the necessary information it may serve to create
the Sardana system in the Tango database. Use the `sardana.py` script to do so:

   `python sardana.py <path-to-fods-file>`

   e.g.

   `python sardana.py blxx.fods`

Several advanced options exists in order to adjust the creation process, so use
the help option in order to discover them:

   `python sardana.py --help`

## Tips & Tricks

* If you want to comment some controllers, motors, etc. in the FODS file, 
  you can do it adding a *#* before the name.
* Some controllers may depend on others e.g. physical axes of one pseudo
  motor controller may be pseudos from another controller. In this case
  the order of controllers in the sheet is important.
