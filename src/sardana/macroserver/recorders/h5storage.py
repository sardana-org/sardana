#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2017 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################


"""This module provides a recorder for NXscans implemented with h5py (no nxs)"""

__all__ = ["NXscanH5_FileRecorder"]

__docformat__ = 'restructuredtext'

import os
from datetime import datetime
import numpy
import h5py

from sardana.taurus.core.tango.sardana import PlotType
from sardana.macroserver.scan.recorder import BaseFileRecorder, SaveModes


class NXscanH5_FileRecorder(BaseFileRecorder):
    """
    Saves data to a nexus file that follows the NXscan application definition
    (This is a pure h5py implementation that does not depend on the nxs module)
    """
    formats = {'h5': '.h5'}
    supported_dtypes = ('float32', 'float64', 'int8',
                        'int16', 'int32', 'int64', 'uint8',
                        'uint16', 'uint32',
                        'uint64')  # note that 'char' is not supported yet!
    # TODO: support 'char'. See http://docs.h5py.org/en/latest/strings.html
    _dataCompressionRank = -1

    def __init__(self, filename=None, macro=None, overwrite=False, **pars):
        BaseFileRecorder.__init__(self, **pars)

        self.macro = macro
        self.overwrite = overwrite
        if filename:
            self.setFileName(filename)

        self.currentlist = None
        self._nxclass_map = {}
        self.entryname = 'entry'

    def getFormat(self):
        return 'HDF5::NXscan'

    def setFileName(self, filename):
        if self.fd is not None:
            self.fd.close()
        self.filename = filename
        self.currentlist = None

    def sanitizeName(self, name):
        """It returns a version of the given name that can be used as a python
        variable (and conforms to NeXus best-practices for dataset names)
        """
        # make sure the name does not start with a digit
        if name[0].isdigit():
            name = "_%s" % name
        # substitute whitespaces by underscores and remove other
        # non-alphanumeric characters
        return "".join(
            x for x in name.replace(' ', '_') if x.isalnum() or x == '_')

    def _openFile(self, fname):
        """Open the file with given filename (create if it does not exist)
        Populate the root of the file with some metadata from the NXroot 
        definition"""
        if os.path.exists(fname):
            fd = h5py.File(fname, mode='r+')
        else:
            fd = h5py.File(fname, mode='w-')
            fd.attrs['NX_class'] = 'NXroot'
            fd.attrs['file_name'] = fname
            fd.attrs['file_time'] = datetime.now().isoformat()
            fd.attrs['creator'] = self.__class__.__name__
            fd.attrs['HDF5_Version'] = h5py.version.hdf5_version
            fd.attrs['h5py_version'] = h5py.version.version
        return fd

    def _startRecordList(self, recordlist):
        
        if self.filename is None:
            return
        
        self.currentlist = recordlist
        env = self.currentlist.getEnviron()
        serialno = env['serialno']
        self._dataCompressionRank = env.get('DataCompressionRank',
                                            self._dataCompressionRank)

        # open/create the file and store its descriptor
        self.fd = self._openFile(self.filename)

        # create an entry for this scan using the scan serial number
        self.entryname = 'entry%d' % serialno
        try:
            nxentry = self.fd.create_group(self.entryname)
        except ValueError:
            # Warn and abort
            if self.entryname in self.fd.keys():
                msg = ('{ename:r} already exists in {fname:r}.' +
                       'Aborting macro to prevent data corruption.\n' +
                       'This is likely caused by a wrong ScanID\n' +
                       'Possible workarounds:\n' +
                       '  * first, try re-running this macro (the ScanID may ' +
                       'be automatically corrected)\n'
                       '  * if not, try changing ScanID with senv, or...\n' +
                       '  * change the file name ({ename:r} will be in both ' +
                       'files containing different data)\n' +
                       '\nPlease report this problem.'
                       ).format(ename=self.entryname, fname=self.filename)
                raise RuntimeError(msg)
            else:
                raise
        nxentry.attrs['NX_class'] = 'NXentry'

        # adapt the datadesc to the NeXus requirements
        self.datadesc = []
        for dd in env['datadesc']:
            dd = dd.clone()
            dd.label = self.sanitizeName(dd.label)
            if dd.dtype == 'bool':
                dd.dtype = 'int8'
                self.debug('%r will be stored with type=%r', dd.name, dd.dtype)
            if dd.dtype in self.supported_dtypes:
                self.datadesc.append(dd)
            else:
                msg = '%r will not be stored. Reason: %r not supported'
                self.warning(msg, dd.name, dd.dtype)
                        
        # make a dictionary out of env['instrumentlist']
        # (use fullnames -paths- as keys)
        self._nxclass_map = {}
        for inst in env.get('instrumentlist', []):
            self._nxclass_map[nxentry.name + inst.getFullName()] = inst.klass
        if self._nxclass_map is {}:
            self.warning('Missing information on NEXUS structure. ' +
                         'Nexus Tree will not be created')
        
        self.debug('Starting new recording %d on file %s', serialno,
                   self.filename)

        # populate the entry with some data
        nxentry.create_dataset('definition', data='NXscan')
        import sardana.release
        program_name = '%s (%s)' % (sardana.release.name,
                                    self.__class__.__name__)
        _pname = nxentry.create_dataset('program_name', data=program_name)
        _pname.attrs['version'] = sardana.release.version
        nxentry.create_dataset('start_time', data=env['starttime'].isoformat())
        _epoch = (env['starttime'] - datetime(1970, 1, 1)).total_seconds()
        nxentry.attrs['epoch'] = _epoch
        nxentry.create_dataset('title', data=env['title'])
        nxentry.create_dataset('entry_identifier', data=str(env['serialno']))

        _usergrp = nxentry.create_group('user')
        _usergrp.attrs['NX_class'] = 'NXuser'
        _usergrp.create_dataset('name', data=env['user'])

        # prepare the 'measurement' group
        _meas = nxentry.create_group('measurement')
        _meas.attrs['NX_class'] = 'NXcollection'
        if self.savemode == SaveModes.Record:
            # create extensible datasets
            for dd in self.datadesc:
                shape = ([0] + list(dd.shape))
                _ds = _meas.create_dataset(
                        dd.label,
                        dtype=dd.dtype,
                        shape=shape,
                        maxshape=([None] + list(dd.shape)),
                        chunks=(1,) + tuple(dd.shape),
                        compression=self._compression(shape)
                        )
                if hasattr(dd, 'data_units'):
                    _ds.attrs['units'] = dd.data_units
                    
        else:
            # leave the creation of the datasets to _writeRecordList
            # (when we actually know the length of the data to write)
            pass
        
        self._createPreScanSnapshot(env)
            
        self.fd.flush()

    def _compression(self, shape, compfilter='gzip'):
        """
        Returns `compfilter` (the name of the compression filter) to use
        (or None if no compression is recommended), based on the given shape
        and the self._dataCompressionRank thresshold.
        By default, `compfilter` is set to `'gzip'`
        """
        min_rank = self._dataCompressionRank
        if shape is None or min_rank < 0 or len(shape) < min_rank:
            return None
        else:
            return compfilter
    
    def _createPreScanSnapshot(self, env):
        """ 
        Write the pre-scan snapshot in "<entry>/measurement/pre_scan_snapshot".
        Also link to the snapshot datasets from the <entry>/measurement group
        """
        _meas = self.fd[os.path.join(self.entryname, 'measurement')]
        self.preScanSnapShot = env.get('preScanSnapShot', [])
        _snap = _meas.create_group('pre_scan_snapshot')
        _snap.attrs['NX_class'] = 'NXcollection'

        meas_keys = _meas.keys()

        for dd in self.preScanSnapShot:
            label = self.sanitizeName(dd.label)
            dtype = dd.dtype
            pre_scan_value = dd.pre_scan_value
            if dd.dtype == 'bool':
                dtype = 'int8'
                pre_scan_value = numpy.int8(dd.pre_scan_value)
                self.debug('Pre-scan snapshot of %s will be stored as type %s',
                           dd.name, dtype)
            if dtype in self.supported_dtypes:
                _ds = _snap.create_dataset(
                        label,
                        data=pre_scan_value,
                        compression=self._compression(dd.shape)
                )
                # link to this dataset also from the measurement group
                if label not in meas_keys:
                    _meas[label] = _ds
            else:
                self.warning(('Pre-scan snapshot of %s will not be stored. ' +
                              'Reason: type %s not supported'),
                             dd.name, dtype)

    def _writeRecord(self, record):
        if self.filename is None:
            return
        _meas = self.fd[os.path.join(self.entryname, 'measurement')]

        for dd in self.datadesc:
            if dd.name in record.data:
                data = record.data[dd.name]
                _ds = _meas[dd.label]
                
                if data is None:
                    data = numpy.zeros(dd.shape, dtype=dd.dtype)
                if not hasattr(data, 'shape'):
                    data = numpy.array([data], dtype=dd.dtype)
                elif dd.dtype != data.dtype.name:
                    self.debug('%s casted to %s (was %s)',
                               dd.label, dd.dtype, data.dtype.name)
                    data = data.astype(dd.dtype)

                # resize the dataset and add the latest chunk
                if _ds.shape[0] <= record.recordno:
                    _ds.resize(record.recordno + 1, axis=0)

                # write the slab of data
                _ds[record.recordno, ...] = data
            else:
                self.debug('missing data for label %r', dd.label)
        self.fd.flush()

    def _endRecordList(self, recordlist):

        if self.filename is None:
            return
        
        self._populateInstrumentInfo()
        self._createNXData()

        env = self.currentlist.getEnviron()
        nxentry = self.fd[self.entryname]
        nxentry.create_dataset('end_time', data=env['endtime'].isoformat())
        self.fd.flush()
        self.debug('Finishing recording %d on file %s:',
                   env['serialno'], self.filename)
        self.fd.close()
        self.currentlist = None

    def writeRecordList(self, recordlist):
        """Called when in BLOCK writing mode"""
        self._startRecordList(recordlist)
        _meas = self.fd[os.path.join(self.entryname, 'measurement')]
        for dd in self.datadesc:
            shape = ([len(recordlist.records)] + list(dd.shape))
            _ds = _meas.create_dataset(
                    dd.label,
                    dtype=dd.dtype,
                    shape=shape,
                    chunks=(1,) + tuple(dd.shape),
                    compression=self._compression(shape)
            )
            if hasattr(dd, 'data_units'):
                _ds.attrs['units'] = dd.data_units

            for record in recordlist.records:
                if dd.label in record.data:
                    _ds[record.recordno, ...] = record.data[dd.label]
                else:
                    self.debug('missing data for label %r in record %i',
                               dd.label, record.recordno)
        self._endRecordList(recordlist)

    def _populateInstrumentInfo(self):
        nxentry = self.fd[self.entryname]
        _meas = nxentry['measurement']
        _snap = _meas['pre_scan_snapshot']
        # create a link for each
        for dd in self.datadesc:
            # we only link if the instrument info is available
            if getattr(dd, 'instrument', None):
                try:
                    _ds = _meas[dd.label]
                    _instr = self._createNXpath(dd.instrument,
                                                prefix=nxentry.name)
                    _instr[os.path.basename(_ds.name)] = _ds
                except Exception, e:
                    msg = 'Could not create link to %r in %r. Reason: %r'
                    self.warning(msg, dd.label, dd.instrument, e)
                    
        for dd in self.preScanSnapShot:
            if getattr(dd, 'instrument', None):
                label = self.sanitizeName(dd.label)
                try:
                    _ds = _snap[label]
                    _instr = self._createNXpath(dd.instrument,
                                                prefix=nxentry.name)
                    _instr[os.path.basename(_ds.name)] = _ds
                except Exception, e:
                    msg = 'Could not create link to %r in %r. Reason: %r'
                    self.warning(msg, label, dd.instrument, e)

    def _createNXData(self):
        """
        Creates groups of type NXdata by making links to the corresponding 
        datasets 
        """
        # classify by type of plot:
        plots1d = {}
        plots1d_names = {}
        i = 1
        for dd in self.datadesc:
            ptype = getattr(dd, 'plot_type', PlotType.No)
            if ptype == PlotType.No:
                continue
            elif ptype == PlotType.Spectrum:
                # converting the list into a colon-separated string
                axes = ':'.join(dd.plot_axes)
                if axes in plots1d:
                    plots1d[axes].append(dd)
                else:
                    plots1d[axes] = [dd]
                    # Note that datatesc ordering determines group name indexing
                    plots1d_names[axes] = 'plot_%i' % i
                    i += 1
            else:
                continue  # TODO: implement support for images and other

        nxentry = self.fd[self.entryname]
        _meas = nxentry['measurement']

        # write the 1D NXdata group
        for axes, v in plots1d.items():
            _nxdata = nxentry.create_group(plots1d_names[axes])
            _nxdata.attrs['NX_class'] = 'NXdata'

            # write the signals
            for i, dd in enumerate(v):
                # link the datasets
                _ds = _nxdata[dd.label] = _meas[dd.label]
                # add attrs
                _ds.attrs['signal'] = min(i + 1, 2)
                _ds.attrs['axes'] = axes
                _ds.attrs['interpretation'] = 'spectrum'
            # write the axes
            for axis in axes.split(':'):
                try:
                    _nxdata[axis] = _meas[axis]
                except:
                    self.warning('cannot create link for "%s". Skipping', axis)

    def _createNXpath(self, path, prefix=None):
        """
        Creates a path in the nexus file composed by nested data_groups
        with their corresponding NXclass attributes.

        This method creates the groups if they do not exist. If the
        path is given using `name:nxclass` notation, the given nxclass is 
        used.
        Otherwise, the class name is obtained from self._nxclass_map values 
        (and if not found, it defaults to NXcollection). 

        It returns the tip of the branch (the last group created)
        """

        if prefix is None:
            # if prefix is None, use current entry if path is relative
            path = os.path.join("/%s:NXentry" % self.entryname, path)
        else:
            # if prefix is given explicitly, assume that path is relative to it
            # even if path is absolute
            path = os.path.join(prefix, path.lstrip('/'))

        grp = self.fd['/']
        for name in path[1:].split('/'):
            if ':' in name:
                name, nxclass = name.split(':')
            else:
                nxclass = None
            # open group (create if it does not exist)
            grp = grp.require_group(name)
            if 'NX_class' not in grp.attrs:
                if nxclass is None:
                    nxclass = self._nxclass_map.get(grp.name, 'NXcollection')
                grp.attrs['NX_class'] = nxclass
        return grp

    def _addCustomData(self, value, name, nxpath=None, dtype=None, **kwargs):
        """
        Apart from value and name, this recorder can use the following optional 
        parameters:
        
        :param nxpath: (str) a nexus path (optionally using name:nxclass 
                       notation for the group names). See the rules for 
                       automatic nxclass resolution used by
                       :meth:`._createNXpath`. If None given, it defaults to 
                       nxpath='custom_data:NXcollection'
                       
        :param dtype: name of data type (it is inferred from value if not given)
                       
        """
        if nxpath is None:
            nxpath = 'custom_data:NXcollection'
        if dtype is None:
            if numpy.isscalar(value):
                dtype = numpy.dtype(type(value)).name
                if numpy.issubdtype(dtype, str):
                    dtype = 'char'
                if dtype == 'bool':
                    value, dtype = int(value), 'int8'
            else:
                value = numpy.array(value)
                dtype = value.dtype.name
            
        if dtype not in self.supported_dtypes and dtype != 'char':
            self.warning('cannot write %r. Reason: unsupported data type', name)
            return

        # open the file if necessary
        fileClosed = self.fd is None or not hasattr(self.fd, 'mode')
        if fileClosed:
            self.fd = self._openFile(self.filename)

        # create the custom data group if it does not exist
        grp = self._createNXpath(nxpath)
        try:
            grp.create_dataset(name, data=value)
        except ValueError, e:
            msg = 'Error writing %s. Reason: %s' % (name, e)
            self.warning(msg)
            self.macro.warning(msg)

        # flush
        self.fd.flush()

        # leave the file as it was
        if fileClosed:
            self.fd.close()
