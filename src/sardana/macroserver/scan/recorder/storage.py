#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This is the macro server scan data output recorder module"""

__all__ = ["AmbiguousRecorderError", "BaseFileRecorder", 
           "BaseNAPI_FileRecorder", "BaseNEXUS_FileRecorder","FileRecorder"]

__docformat__ = 'restructuredtext'

import os
import time
import itertools
import re

import numpy

import PyTango

from sardana.taurus.core.tango.sardana import PlotType
from sardana.macroserver.macro import Type
from sardana.macroserver.scan.recorder.datarecorder import DataRecorder, \
    SaveModes
from sardana.macroserver.msexception import MacroServerException
from taurus.core.util.containers import chunks


class AmbiguousRecorderError(MacroServerException):
    pass


class BaseFileRecorder(DataRecorder):
    def __init__(self, **pars):
        DataRecorder.__init__(self, **pars)
        self.filename = None
        self.fd       = None 
        
    def getFileName(self):
        return self.filename

    def getFileObj(self):
        return self.fd

    def getFormat(self):
        return '<unknown>'


class BaseNEXUS_FileRecorder(BaseFileRecorder):
    """Base class for NeXus file recorders"""   
    
    formats = {'w5': '.h5',
               'w4': '.h4',
               'wx': '.xml'}
    supported_dtypes = ('float32','float64','int8',
                        'int16','int32','int64','uint8',
                        'uint16','uint32','uint64') #note that 'char' is not supported yet!
    _dataCompressionRank = -1
        
    def __init__(self, filename=None, macro=None, overwrite=False, **pars):
        BaseFileRecorder.__init__(self, **pars)

        try:
            import nxs  #check if Nexus data format is supported by this system
            self.nxs = nxs
        except ImportError:
            raise Exception("NeXus is not available")
        
        self.macro = macro
        self.overwrite = overwrite
        if filename:
            self.setFileName(filename)
            
        self.instrDict = {}
        self.entryname = 'entry'
    
    def setFileName(self, filename):
        if self.fd  is not None:
            self.fd.close()
   
        self.filename = filename
        #obtain preferred nexus file mode for writing from the filename extension (defaults to hdf5)
        extension = os.path.splitext(filename)[1]
        inv_formats = dict(itertools.izip(self.formats.itervalues(), self.formats.iterkeys()))
        self.nxfilemode = inv_formats.get(extension.lower(), 'w5')
        self.currentlist = None
    
    def getFormat(self):
        return self.nxfilemode
    
    def sanitizeName(self, name):
        '''It returns a version of the given name that can be used as a python
        variable (and conforms to NeXus best-practices for dataset names)'''
        #make sure the name does not start with a digit
        if name[0].isdigit(): name = "_%s" % name
        #substitute whitespaces by underscores and remove other non-alphanumeric characters
        return "".join(x for x in name.replace(' ','_') if x.isalnum() or x=='_')
    
    
    def _nxln(self, src, dst, name=None):
        '''convenience function to create NX links with just one call. On successful return, dst will be open.
        
        :param src: (str or NXgroup or NXfield) source group or dataset (or its path)
        :param dst: (str or NXgroup) the group that will hold the link (or its path)
        :param name: (str) name for the link. If not given, the name of the source is used
        
        .. note:: `groupname:nxclass` notation can be used for both paths for better performance
        '''
        
        fd = getattr(self, 'fd')
        if fd is None:
            fd = getattr(src,'nxfile', getattr(dst,'nxfile'))
        if fd is None:
            raise self.nxs.NeXusError('Cannot get a file handle')
        
        if isinstance(src, self.nxs.NXobject):
            src = src.nxpath
        if isinstance(dst, self.nxs.NXobject):
            dst = dst.nxpath
            
        fd.openpath(src)
        try:
            nid = fd.getdataID()
        except self.nxs.NeXusError:
            nid = fd.getgroupID()
        fd.openpath(dst)
        if name is None:
            fd.makelink(nid)
        else:
            fd.makenamedlink(name,nid)

    #===========================================================================
    # Unimplemented methods that must be implemented in derived classes    
    #===========================================================================
    
    def _startRecordList(self, recordlist):
        raise NotImplementedError('_startRecordList must be implemented in BaseNEXUS_FileRecorder derived classes')    
    
    def _writeRecord(self, record):
        raise NotImplementedError('_writeRecord must be implemented in BaseNEXUS_FileRecorder derived classes')  
    
    def _endRecordList(self, recordlist):
        raise NotImplementedError('_endRecordList must be implemented in BaseNEXUS_FileRecorder derived classes')  


class BaseNAPI_FileRecorder(BaseNEXUS_FileRecorder):
    """Base class for NeXus file recorders (NAPI-based)"""
    
    #===========================================================================
    # Convenience methods to make NAPI less tedious
    #===========================================================================
    
    _nxentryInPath = re.compile(r'/[^/:]+:NXentry')
    
    def _makedata(self, name, dtype=None, shape=None, mode='lzw', chunks=None, comprank=None):
        '''
        combines :meth:`nxs.NeXus.makedata` and :meth:`nxs.NeXus.compmakedata` by selecting between 
        using compression or not based on the comprank parameter and the rank of the data.
        Compression will be used only if the shape of the data is given and its length is larger 
        than comprank. If comprank is not passed (or None is passed) the default dataCompressionRank 
        will be used
        '''
        if comprank is None: 
            comprank = self._dataCompressionRank
        
        if shape is None or comprank<0 or (len(shape) < comprank):
            return self.fd.makedata(name, dtype=dtype, shape=shape)
        else:
            try:
                self.fd.compmakedata(name, dtype=dtype, shape=shape, mode=mode, chunks=chunks)
            except ValueError: #workaround for bug in nxs<4.3 (compmakedatafails if chunks is not explicitly passed)
                chunks = [1]*len(shape)
                chunks[-1] = shape[-1]
                self.fd.compmakedata(name, dtype=dtype, shape=shape, mode=mode, chunks=chunks)
              
    def _writeData(self, name, data, dtype, shape=None, chunks=None, attrs=None):
        '''
        convenience method that creates datasets (calling self._makedata), opens
        it (napi.opendata) and writes the data (napi.putdata).
        It also writes attributes (napi.putattr) if passed in a dictionary and 
        it returns the data Id (useful for linking). The dataset is left closed. 
        '''
        if shape is None:
            if dtype == 'char':
                shape = [len(data)]
                chunks = chunks or list(shape) #for 'char', write the whole block in one chunk
            else:
                shape = getattr(data,'shape',[1])
        self._makedata(name, dtype=dtype, shape=shape, chunks=chunks)
        self.fd.opendata(name)
        self.fd.putdata(data)
        if attrs is not None:
            for k,v in attrs.items():
                self.fd.putattr(k,v)
        nid = self.fd.getdataID()
        self.fd.closedata()
        return nid

    def _newentryname(self, prefix='entry', suffix='', offset=1):
        '''Returns a str representing the name for a new entry.
        The name is formed by the prefix and an incremental numeric suffix.
        The offset indicates the start of the numeric suffix search'''
        i = offset
        while True:
            entry = "%s%i" % (prefix, i)
            if suffix:
                entry += " - " + suffix
            try:
                self.fd.opengroup(entry,'NXentry')
                self.fd.closegroup()
                i += 1
            except ValueError:  #no such group name exists
                return entry
        
    def _nxln(self, src, dst):
        '''convenience function to create NX links with just one call. On successful return, dst will be open.
        
        :param src: (str) the nxpath to the source group or dataset
        :param dst: (str) the nxpath to the group that will hold the link
        
        .. note:: `groupname:nxclass` notation can be used for both paths for better performance
        '''
        self.fd.openpath(src)
        try:
            nid = self.fd.getdataID()
        except self.nxs.NeXusError:
            nid = self.fd.getgroupID()
        self.fd.openpath(dst)
        self.fd.makelink(nid)
            
    def _createBranch(self, path):
        """
        Navigates the nexus tree starting in / and finishing in path. 
        
        If path does not start with `/<something>:NXentry`, the current entry is
        prepended to it.
        
        This method creates the groups if they do not exist. If the
        path is given using `name:nxclass` notation, the given nxclass is used.
        Otherwise, the class name is obtained from self.instrDict values (and if
        not found, it defaults to NXcollection). If successful, path is left
        open
        """
        m = self._nxentryInPath.match(path)
        if m is None:
            self._createBranch("/%s:NXentry" % self.entryname)  #if at all, it will recurse just once
#            self.fd.openpath("/%s:NXentry" % self.entryname)
        else:
            self.fd.openpath("/")

        relpath = ""
        for g in path.split('/'):
            if len(g) == 0:
                continue
            relpath = relpath + "/"+ g
            if ':' in g:
                g,group_type = g.split(':')
            else:
                try:
                    group_type = self.instrDict[relpath].klass
                except:
                    group_type = 'NXcollection'
            try:
                self.fd.opengroup(g, group_type)
            except:
                self.fd.makegroup(g, group_type)
                self.fd.opengroup(g, group_type)


def FileRecorder(filename, macro, **pars):
    ext = os.path.splitext(filename)[1].lower() or '.spec'
    rec_manager = macro.getMacroServer().recorder_manager

    hinted_recorder = getattr(macro, 'hints', {}).get('FileRecorder', None)
    if hinted_recorder is not None:
        macro.deprecated("FileRecorder macro hints are deprecated. "
                         "Use ScanRecorder variable instead.")
        klass = rec_manager.getRecorderClass(hinted_recorder)
    else:
        klasses = rec_manager.getRecorderClasses(
            filter=BaseFileRecorder, extension=ext)
        len_klasses = len(klasses)
        if len_klasses == 0:
            klass = rec_manager.getRecorderClass('SPEC_FileRecorder')
        elif len_klasses == 1:
            klass = klasses.values()[0]
        else:
            raise AmbiguousRecorderError('Choice of recorder for %s '
                                         'extension is ambiguous' % ext)
    return klass(filename=filename, macro=macro, **pars)
