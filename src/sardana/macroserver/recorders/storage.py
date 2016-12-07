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

__all__ = ["FIO_FileRecorder", "NXscan_FileRecorder", "SPEC_FileRecorder"]

__docformat__ = 'restructuredtext'

import os
import time
import itertools
import re

import numpy

import PyTango

from sardana.taurus.core.tango.sardana import PlotType
from sardana.macroserver.macro import Type
from sardana.macroserver.scan.recorder import (BaseFileRecorder,
                                               BaseNAPI_FileRecorder,
                                               SaveModes)
from taurus.core.util.containers import chunks


class FIO_FileRecorder(BaseFileRecorder):
    """ Saves data to a file """

    formats = {'fio': '.fio'}

    def __init__(self, filename=None, macro=None, **pars):
        BaseFileRecorder.__init__(self)
        self.base_filename = filename
        if macro:
            self.macro = macro
        self.db = PyTango.Database()
        if filename:
            self.setFileName(self.base_filename)

    def setFileName(self, filename):
        if self.fd != None: 
            self.fd.close()
   
        dirname = os.path.dirname(filename)
        
        if not os.path.isdir(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.filename = None
                return
        self.currentlist = None
        #
        # construct the filename, e.g. : /dir/subdir/etcdir/prefix_00123.fio
        #
        tpl = filename.rpartition('.')
        try: # For avoiding error when calling at __init__
            serial = self.recordlist.getEnvironValue('serialno')
            self.filename = "%s_%05d.%s" % (tpl[0], serial, tpl[2])
            #
            # in case we have MCAs, prepare the dir name
            #
            self.mcaDirName = "%s_%05d" % (tpl[0], serial)
        except:
            self.filename = "%s_%s.%s" % (tpl[0], "[ScanId]", tpl[2])

    def getFormat(self):
        return self.formats.keys()[0]
    
    def _startRecordList(self, recordlist):

        if self.base_filename is None:
            return

        self.setFileName(self.base_filename)
        
        envRec = recordlist.getEnviron()

        self.sampleTime = envRec['estimatedtime'] / (envRec['total_scan_intervals'] + 1)
        #datetime object
        start_time = envRec['starttime']
        
        self.motorNames = envRec[ 'ref_moveables']
        self.mcaNames = []
        self.ctNames = []
        for e in envRec['datadesc']:
            if len( e.shape) == 1:
                self.mcaNames.append( e.name)
            else:
                self.ctNames.append( e.name)
        #
        # we need the aliases for the column description
        #
        self.mcaAliases = []
        for mca in self.mcaNames:
            lst = mca.split("/")
            self.mcaAliases.append( self.db.get_alias( "/".join( lst[1:])))

        # self.names = [ e.name for e in envRec['datadesc'] ]
        self.fd = open( self.filename,'w')
        #
        # write the comment section of the header
        #
        self.fd.write("!\n! Comments\n!\n%%c\n %s\nuser %s Acquisition started at %s\n" % 
                      (envRec['title'], envRec['user'], start_time.ctime()))
        self.fd.flush()
        #
        # write the parameter section, including the motor positions, if needed
        #
        self.fd.write("!\n! Parameter\n!\n%p\n")
        self.fd.flush()
        env = self.macro.getAllEnv()
        if env.has_key( 'FlagFioWriteMotorPositions') and env['FlagFioWriteMotorPositions'] == True:
            all_motors = self.macro.findObjs('.*', type_class=Type.Motor)
            all_motors.sort()
            for mot in all_motors:
                pos = mot.getPosition()
                if pos is None:
                    record = "%s = nan\n" % (mot)
                else:
                    record = "%s = %g\n" % (mot, mot.getPosition())
                    
                self.fd.write( record)
            self.fd.flush()
        #
        # write the data section starting with the description of the columns
        #
        self.fd.write("!\n! Data\n!\n%d\n")
        self.fd.flush()
        i = 1
        for col in envRec[ 'datadesc']:
            if col.name == 'point_nb':
                continue
            if col.name == 'timestamp':
                continue
            dType = 'FLOAT'
            if col.dtype == 'float64':
                dType = 'DOUBLE'
            outLine = " Col %d %s %s\n" % ( i, col.label, dType)
            self.fd.write( outLine)
            i += 1
        #
        # 11.9.2012 timestamp to the end
        #
        outLine = " Col %d %s %s\n" % ( i, 'timestamp', 'DOUBLE')
        self.fd.write( outLine)

        self.fd.flush()

    def _writeRecord(self, record):
        if self.filename is None:
            return
        nan, ctNames, fd = float('nan'), self.ctNames, self.fd
        outstr = ''
        for c in ctNames:
            if c == "timestamp" or c == "point_nb":
                continue
            outstr += ' ' + str(record.data.get(c, nan))
        #
        # 11.9.2012 timestamp to the end
        #
        outstr += ' ' + str(record.data.get('timestamp', nan))
        outstr += '\n'
        
        fd.write( outstr )
        fd.flush()

        if len( self.mcaNames) > 0:
            self._writeMcaFile( record)

    def _endRecordList(self, recordlist):
        if self.filename is None:
            return

        envRec = recordlist.getEnviron()
        end_time = envRec['endtime'].ctime()
        self.fd.write("! Acquisition ended at %s\n" % end_time)
        self.fd.flush()
        self.fd.close()

    def _writeMcaFile( self, record):
        if self.mcaDirName is None:
            return

        if not os.path.isdir( self.mcaDirName):
            try:
                os.makedirs( self.mcaDirName)
            except:
                self.mcaDirName = None
                return
        currDir = os.getenv( 'PWD')
        os.chdir( self.mcaDirName)

        serial = self.recordlist.getEnvironValue('serialno')
        if type(self.recordlist.getEnvironValue('ScanFile')).__name__ == 'list':
            scanFile = self.recordlist.getEnvironValue('ScanFile')[0]
        else:
            scanFile = self.recordlist.getEnvironValue('ScanFile')

        mcaFileName = "%s_%05d_mca_s%d.fio" % (scanFile.split('.')[0], serial, record.data['point_nb'] + 1)
        fd = open( mcaFileName,'w')
        fd.write("!\n! Comments\n!\n%%c\n Position %g, Index %d \n" % 
                      ( record.data[ self.motorNames[0]], record.data[ 'point_nb']))
        fd.write("!\n! Parameter \n%%p\n Sample_time = %g \n" % ( self.sampleTime))
        self.fd.flush()

        col = 1
        fd.write("!\n! Data \n%d \n")
        for mca in self.mcaAliases:
            fd.write(" Col %d %s FLOAT \n" % (col, mca))
            col = col + 1

        if not record.data[ self.mcaNames[0]] is None:
            #print "+++storage.py, recordno", record.recordno
            #print "+++storage.py, record.data", record.data
            #print "+++storage.py, len %d,  %s" % (len( record.data[ self.mcaNames[0]]), self.mcaNames[0])
            #
            # the MCA arrays me be of different size. the short ones are extended by zeros.
            #
            lMax = len( record.data[ self.mcaNames[0]])
            for mca in self.mcaNames:
                if len(record.data[ mca]) > lMax:
                    lMax = len(record.data[ mca])
                    
            for i in range( 0, lMax):
                line = ""
                for mca in self.mcaNames:
                    if i > (len(record.data[mca]) - 1):
                        line = line + " 0"
                    else:
                        line = line + " " + str( record.data[ mca][i])
                line = line + "\n"
                fd.write(line)
            
            fd.close()
        else:
            #print "+++storage.py, recordno", record.recordno, "data None"
            pass
            
        os.chdir( currDir)

class SPEC_FileRecorder(BaseFileRecorder):
    """ Saves data to a file """

    formats = {'Spec': '.spec'}
    supported_dtypes = ('float32','float64','int8',
                        'int16','int32','int64','uint8',
                        'uint16','uint32','uint64')

    def __init__(self, filename=None, macro=None, **pars):
        BaseFileRecorder.__init__(self)
        if filename:
            self.setFileName(filename)
    
    def setFileName(self, filename):
        if self.fd != None:
            self.fd.close()
   
        dirname = os.path.dirname(filename)
        
        if not os.path.isdir(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.filename = None
                return
        self.filename    = filename
        self.currentlist = None

    def getFormat(self):
        return self.formats.keys()[0]
    
    def _startRecordList(self, recordlist):
        '''Prepares and writes the scan header.'''
        if self.filename is None:
            return

        env = recordlist.getEnviron()
        
        #datetime object
        start_time = env['starttime']
        epoch = time.mktime(start_time.timetuple())
        serialno = env['serialno']
        
        #store names for performance reason
        labels = []
        names = []
        oned_labels = []
        oned_names = []
        oned_shape = 0
        for e in env['datadesc']:
            dims = len(e.shape)
            if dims >= 2:
                continue
            sanitizedlabel = "".join(x for x in e.label.replace(' ', '_') if x.isalnum() or x == '_')  #substitute whitespaces by underscores and remove other non-alphanumeric characters
            if not dims or (dims == 1 and e.shape[0] == 1):
                labels.append(sanitizedlabel)
                names.append(e.name)
            else:
                oned_labels.append(sanitizedlabel)
                oned_names.append(e.name)
                oned_shape = e.shape[0]

        self.names = names
        self.oned_names = oned_names

        # prepare pre-scan snapshot
        snapshot_labels, snapshot_values = self._preparePreScanSnapshot(env)
        # format scan header
        data = {
                'serialno':  serialno,
                'title':     env['title'],
                'user':      env['user'],
                'epoch':     epoch,
                'starttime': start_time.ctime(),
                'nocols':    len(names),
                'labels':    '  '.join(labels)
               }
        #Compatibility with PyMca
        if os.path.exists(self.filename):
            header = '\n'
        else:
            header = ''
        header += '#S %(serialno)s %(title)s\n'
        header += '#U %(user)s\n'
        header += '#D %(epoch)s\n'
        header += '#C Acquisition started at %(starttime)s\n'
        # add a pre-scan snapshot (sep is two spaces for labels!!)
        header += self._prepareMultiLines('O', '  ', snapshot_labels)
        header += self._prepareMultiLines('P', ' ', snapshot_values)
        header += '#N %(nocols)s\n'
        if len(oned_labels) > 0:
            header += '#@MCA %sC\n' % oned_shape
            header += '#@CHANN %s 0 %s 1\n' % (oned_shape, oned_shape-1)
            header += '#@MCA_NB %s\n' % len(oned_labels)
            for idx, oned_label in enumerate(oned_labels):
                header += '#@DET_%s %s\n' %(idx, oned_label)
        header += '#L %(labels)s\n'
        
        self.fd = open(self.filename,'a')
        self.fd.write(header % data )
        self.fd.flush()
        
    def _prepareMultiLines(self, character, sep, items_list):
        '''Translate list of lists of items into multiple line string
        
        :param character (string): each line will start #<character><line_nr>
        :sep: separator (string): separator to use between items
        :param items_list (list):list of lists of items
        
        :return multi_lines (string): string with all the items'''
        multi_lines = ''
        for nr, items in enumerate(items_list):
            start = '#%s%d ' % (character, nr)
            items_str = sep.join(map(str, items))
            end = '\n'
            line = start + items_str + end
            multi_lines += line 
        return multi_lines
    
    def _preparePreScanSnapshot(self, env):
        '''Extract pre-scan snapshot, filters elements of shape different 
        than scalar and split labels and values into chunks of 8 items.
        
        :param: env (dict) scan environment
        
        :return: labels, values (tuple<list,list>)
                 labels - list of chunks with 8 elements containing labels 
                 values - list of chunks with 8 elements containing values    
        '''
        # preScanSnapShot is a list o ColumnDesc objects
        pre_scan_snapshot = env.get('preScanSnapShot',[])
        labels = []; values = []
        for column_desc in pre_scan_snapshot:
            shape = column_desc.shape # shape is a tuple of dimensions
            label = column_desc.label
            dtype = column_desc.dtype
            pre_scan_value = column_desc.pre_scan_value
            # skip items with shape different than scalar
            if  len(shape) > 0:
                self.info('Pre-scan snapshot of "%s" will not be stored.' + \
                          ' Reason: value is non-scalar', label)
                continue
            if dtype not in self.supported_dtypes:
                self.info('Pre-scan snapshot of "%s" will not be stored.' + \
                          ' Reason: type %s not supported', label, dtype)
                continue
            labels.append(label)
            values.append(pre_scan_value)
        # split labels in chunks o 8 items
        labels_chunks = list(chunks(labels, 8))
        values_chunks = list(chunks(values, 8))
        return labels_chunks, values_chunks
        
    def _writeRecord(self, record):
        if self.filename is None:
            return
        nan, names, fd = float('nan'), self.names, self.fd
        
        d = []
        for oned_name in self.oned_names:
            data = record.data.get(oned_name)
            # TODO: The method astype of numpy does not work properly on the
            # beamline, we found difference between the data saved on h5 and
            # spec. For that reason we implement the it by hand.
            #str_data = ' '.join(data.astype(str))
            str_data = ''
            for i in data:
                str_data += '%s ' % i
            outstr  = '@A %s' % str_data
            outstr += '\n'
            fd.write( outstr )

        for c in names:
            data = record.data.get(c)
            if data is None: data = nan
            d.append(str(data))
        outstr  = ' '.join(d)
        outstr += '\n'
        
        fd.write( outstr )

        fd.flush()

    def _endRecordList(self, recordlist):
        if self.filename is None:
            return

        env = recordlist.getEnviron()
        end_time = env['endtime'].ctime()
        self.fd.write("#C Acquisition ended at %s\n" % end_time)
        self.fd.flush()
        self.fd.close()

                    
    def _addCustomData(self, value, name, **kwargs):
        '''
        The custom data will be added as a comment line in the form:: 
        
        #C name : value
        
        ..note:: non-scalar values (or name/values containing end-of-line) will not be written
        '''
        if self.filename is None:
            self.info('Custom data "%s" will not be stored in SPEC file. Reason: uninitialized file',name)
            return
        if numpy.rank(value) > 0:  #ignore non-scalars
            self.info('Custom data "%s" will not be stored in SPEC file. Reason: value is non-scalar', name)
            return
        v = str(value)
        if '\n' in v or '\n' in name: #ignore if name or the string representation of the value contains end-of-line
            self.info('Custom data "%s" will not be stored in SPEC file. Reason: unsupported format',name)
            return
        
        fileWasClosed = self.fd is None or self.fd.closed
        if fileWasClosed:
            try:
                self.fd = open(self.filename,'a')
            except:
                self.info('Custom data "%s" will not be stored in SPEC file. Reason: cannot open file',name)
                return
        self.fd.write('#C %s : %s\n' % (name, v))
        self.fd.flush()
        if fileWasClosed:
            self.fd.close() #leave the file descriptor as found


class NXscan_FileRecorder(BaseNAPI_FileRecorder):
    """saves data to a nexus file that follows the NXscan application definition
    
        """

    def __init__(self, filename=None, macro=None, overwrite=False, **pars):
        BaseNAPI_FileRecorder.__init__(self, filename=filename, macro=macro, overwrite=overwrite, **pars)
            
    def _startRecordList(self, recordlist):
        nxs = self.nxs
        nxfilemode = self.getFormat()
        
        if self.filename is None:
            return
        
        self.currentlist = recordlist
        env = self.currentlist.getEnviron()
        serialno = env["serialno"]
        self._dataCompressionRank = env.get("DataCompressionRank", self._dataCompressionRank)
        
        if not self.overwrite and os.path.exists(self.filename): nxfilemode='rw'
        self.fd = nxs.open(self.filename, nxfilemode)
        self.entryname = "entry%d" % serialno
        try:
            self.fd.makegroup(self.entryname,"NXentry")
        except self.nxs.NeXusError:
            entrynames = self.fd.getentries().keys()
            
            #===================================================================
            ##Warn and abort
            if self.entryname in entrynames:
                raise RuntimeError(('"%s" already exists in %s. To prevent data corruption the macro will be aborted.\n'%(self.entryname, self.filename)+
                                    'This is likely caused by a wrong ScanID\n'+
                                    'Possible workarounds:\n'+
                                    '  * first, try re-running this macro (the ScanID may be automatically corrected)\n'
                                    '  * if not, try changing ScanID with senv, or...\n'+
                                    '  * change the file name (%s will be in both files containing different data)\n'%self.entryname+
                                    '\nPlease report this problem.'))
            else:
                raise              
            #===================================================================
            
            #===================================================================
            ## Warn and continue writing to another entry
            #if self.entryname in entrynames:
            #    i = 2
            #    newname = "%s_%i"%(self.entryname,i)
            #    while(newname in entrynames):
            #        i +=1
            #        newname = "%s_%i"%(self.entryname,i)
            #    self.warning('"%s" already exists. Using "%s" instead. This may indicate a bug in %s',self.entryname, newname, self.macro.name)
            #    self.macro.warning('"%s" already exists. Using "%s" instead. \nThis may indicate a bug in %s. Please report it.',self.entryname, newname, self.macro.name)
            #    self.entryname = newname
            #    self.fd.makegroup(self.entryname,"NXentry")
            #===================================================================
            
        self.fd.opengroup(self.entryname,"NXentry") 
        
        
        #adapt the datadesc to the NeXus requirements
        self.datadesc = []
        for dd in env['datadesc']:
            dd = dd.clone()
            dd.label = self.sanitizeName(dd.label)
            if dd.dtype == 'bool':
                dd.dtype = 'int8'
                self.debug('%s will be stored with type=%s',dd.name,dd.dtype)
            if dd.dtype in self.supported_dtypes:
                self.datadesc.append(dd)
            else:
                self.warning('%s will not be stored. Reason: type %s not supported',dd.name,dd.dtype)
                        
        #make a dictionary out of env['instrumentlist'] (use fullnames -paths- as keys)
        self.instrDict = {}
        for inst in env.get('instrumentlist', []):
            self.instrDict[inst.getFullName()] = inst
        if self.instrDict is {}:
            self.warning("missing information on NEXUS structure. Nexus Tree won't be created")
        
        self.debug("starting new recording %d on file %s", env['serialno'], self.filename)

        #populate the entry with some data
        self._writeData('definition', 'NXscan', 'char') #this is the Application Definition for NeXus Generic Scans
        import sardana.release
        program_name = "%s (%s)" % (sardana.release.name, self.__class__.__name__)
        self._writeData('program_name', program_name, 'char', attrs={'version':sardana.release.version})
        self._writeData("start_time",env['starttime'].isoformat(),'char') #note: the type should be NX_DATE_TIME, but the nxs python api does not recognize it
        self.fd.putattr("epoch",time.mktime(env['starttime'].timetuple()))
        self._writeData("title",env['title'],'char')
        self._writeData("entry_identifier",str(env['serialno']),'char')
        self.fd.makegroup("user","NXuser") #user data goes in a separate group following NX convention...
        self.fd.opengroup("user","NXuser")
        self._writeData("name",env['user'],'char')
        self.fd.closegroup()
        
        #prepare the "measurement" group
        self._createBranch("measurement:NXcollection")
        if self.savemode == SaveModes.Record:
            #create extensible datasets
            for dd in self.datadesc:
                self._makedata(dd.label, dd.dtype, [nxs.UNLIMITED] + list(dd.shape), chunks=[1] + list(dd.shape))  #the first dimension is extensible
                if hasattr(dd, 'data_units'):
                    self.fd.opendata(dd.label)
                    self.fd.putattr('units', dd.data_units)
                    self.fd.closedata()
                    
        else:
            #leave the creation of the datasets to _writeRecordList (when we actually know the length of the data to write)
            pass
        
        self._createPreScanSnapshot(env)
            
        self.fd.flush()
    
    def _createPreScanSnapshot(self, env):
        #write the pre-scan snapshot in the "measurement:NXcollection/pre_scan_snapshot:NXcollection" group
        self.preScanSnapShot = env.get('preScanSnapShot',[])
        self._createBranch('measurement:NXcollection/pre_scan_snapshot:NXcollection')
        links = {}
        for dd in self.preScanSnapShot: #desc is a ColumnDesc object
            label = self.sanitizeName(dd.label)
            dtype = dd.dtype
            pre_scan_value = dd.pre_scan_value
            if dd.dtype == 'bool':
                dtype = 'int8'
                pre_scan_value = numpy.int8(dd.pre_scan_value)
                self.debug('Pre-scan snapshot of %s will be stored with type=%s',dd.name, dtype)
            if dtype in self.supported_dtypes:
                nid = self._writeData(label, pre_scan_value, dtype, shape=dd.shape or (1,)) #@todo: fallback shape is hardcoded!
                links[label] = nid
            else:
                self.warning('Pre-scan snapshot of %s will not be stored. Reason: type %s not supported',dd.name, dtype)
                
        self.fd.closegroup() #we are back at the measurement group
        
        measurement_entries = self.fd.getentries()
        for label,nid in links.items():
            if label not in measurement_entries:
                self.fd.makelink(nid)
         
    def _writeRecord(self, record):
        if self.filename is None:
            return
        # most used variables in the loop
        fd, debug, warning = self.fd, self.debug, self.warning
        nparray, npshape = numpy.array, numpy.shape
        rec_data, rec_nb = record.data, record.recordno
        
        for dd in self.datadesc:
            if record.data.has_key( dd.name ):
                data = rec_data[dd.name]
                fd.opendata(dd.label)
                
                if data is None:
                    data = numpy.zeros(dd.shape, dtype=dd.dtype)
                if not hasattr(data, 'shape'):
                    data = nparray([data], dtype=dd.dtype)
                elif dd.dtype != data.dtype.name:
                    debug('%s casted to %s (was %s)', dd.label, dd.dtype,
                                                      data.dtype.name)
                    data = data.astype(dd.dtype)

                slab_offset = [rec_nb] + [0] * len(dd.shape)
                shape = [1] + list(npshape(data))
                try:
                    fd.putslab(data, slab_offset, shape)
                except:
                    warning("Could not write <%s> with shape %s", data, shape)
                    raise
                    
                ###Note: the following 3 lines of code were substituted by the one above.
                ###      (now we trust the datadesc info instead of asking the nxs file each time)
                #shape,dtype=self.fd.getinfo()
                #shape[0]=1 #the shape of the record is of just 1 slab in the extensible dimension (first dim)
                #self.fd.putslab(record.data[lbl],[record.recordno]+[0]*(len(shape)-1),shape)
                fd.closedata()
            else:
                debug("missing data for label '%s'", dd.label)
        fd.flush()

    def _endRecordList(self, recordlist):

        if self.filename is None:
            return
        
        self._populateInstrumentInfo()
        self._createNXData()

        env = self.currentlist.getEnviron()
        self.fd.openpath("/%s:NXentry" % self.entryname)
        self._writeData("end_time",env['endtime'].isoformat(),'char')
        self.fd.flush()
        self.debug("Finishing recording %d on file %s:", env['serialno'], self.filename)
        #self.fd.show('.') #prints nexus file summary on stdout (only the current entry)
        self.fd.close()
        self.currentlist = None

    def writeRecordList(self, recordlist):
        """Called when in BLOCK writing mode"""
        self._startRecordList( recordlist )
        for dd in self.datadesc:
            self._makedata(dd.label, dd.dtype, [len(recordlist.records)]+list(dd.shape), chunks=[1]+list(dd.shape))
            self.fd.opendata(dd.label)
            try:
                #try creating a single block to write it at once
                block=numpy.array([r.data[dd.label] for r in recordlist.records],dtype=dd.dtype)
                #if dd.dtype !='char': block=numpy.array(block,dtype=dtype) #char not supported anyway
                self.fd.putdata(block)
            except KeyError:
                #if not all the records contain this field, we cannot write it as a block.. so do it record by record (but only this field!)
                for record in recordlist.records:
                    if record.data.has_key( dd.label ):
                        self.fd.putslab(record.data[dd.label],[record.recordno]+[0]*len(dd.shape),[1]+list(dd.shape)) 
                    else:
                        self.debug("missing data for label '%s' in record %i", dd.label, record.recordno)
            self.fd.closedata()
        self._endRecordList( recordlist )

    def _populateInstrumentInfo(self):
        measurementpath = "/%s:NXentry/measurement:NXcollection" % self.entryname
        #create a link for each
        for dd in self.datadesc:
            if getattr(dd, 'instrument', None):  #we don't link if it is None or it is empty
                try:
                    datapath = "%s/%s" % (measurementpath, dd.label)
                    self.fd.openpath(datapath)
                    nid = self.fd.getdataID()
                    self._createBranch(dd.instrument)
                    self.fd.makelink(nid)
                except Exception,e:
                    self.warning("Could not create link to '%s' in '%s'. Reason: %s",datapath, dd.instrument, repr(e))
                    
        for dd in self.preScanSnapShot:
            if getattr(dd,'instrument', None):
                try:
                    label = self.sanitizeName(dd.label)
                    datapath = "%s/pre_scan_snapshot:NXcollection/%s" % (measurementpath, label)
                    self.fd.openpath(datapath)
                    nid = self.fd.getdataID()
                    self._createBranch(dd.instrument)
                    self.fd.makelink(nid)
                except Exception,e:
                    self.warning("Could not create link to '%s' in '%s'. Reason: %s",datapath, dd.instrument, repr(e))
                
    def _createNXData(self):
        '''Creates groups of type NXdata by making links to the corresponding datasets 
        '''        
        #classify by type of plot:
        plots1d = {}
        plots1d_names = {}
        i = 1
        for dd in self.datadesc:
            ptype = getattr(dd, 'plot_type', PlotType.No)
            if ptype == PlotType.No:
                continue
            elif ptype == PlotType.Spectrum:
                axes = ":".join(dd.plot_axes) #converting the list into a colon-separated string
                if axes in plots1d:
                    plots1d[axes].append(dd)
                else:
                    plots1d[axes] = [dd]
                    plots1d_names[axes] = 'plot_%i' % i  #Note that datatesc ordering determines group name indexing
                    i += 1
            else:
                continue  #@todo: implement support for images and other
        
        #write the 1D NXdata group
        for axes, v in plots1d.items():
            self.fd.openpath("/%s:NXentry" % (self.entryname))
            groupname = plots1d_names[axes]
            self.fd.makegroup(groupname,'NXdata')
            #write the signals
            for i, dd in enumerate(v):
                src = "/%s:NXentry/measurement:NXcollection/%s" % (self.entryname, dd.label)
                dst = "/%s:NXentry/%s:NXdata" % (self.entryname, groupname)
                self._nxln(src, dst)
                self.fd.opendata(dd.label)
                self.fd.putattr('signal', min(i + 1, 2))
                self.fd.putattr('axes', axes)
                self.fd.putattr('interpretation', 'spectrum')
            #write the axes
            for axis in axes.split(':'):
                src = "/%s:NXentry/measurement:NXcollection/%s" % (self.entryname, axis)
                dst = "/%s:NXentry/%s:NXdata" % (self.entryname, groupname)
                try:
                    self._nxln(src, dst)
                except:
                    self.warning("cannot create link for '%s'. Skipping",axis)
                    
    def _addCustomData(self, value, name, nxpath=None, dtype=None, **kwargs):
        '''
        apart from value and name, this recorder can use the following optional parameters:
        
        :param nxpath: (str) a nexus path (optionally using name:nxclass notation for
                       the group names). See the rules for automatic nxclass
                       resolution used by
                       :meth:`NXscan_FileRecorder._createBranch`.
                       If None given, it defaults to 
                       nxpath='custom_data:NXcollection'
                       
        :param dtype: name of data type (it is inferred from value if not given)
                       
        '''           
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
            self.warning("cannot write '%s'. Reason: unsupported data type",name)
            return
        #open the file if necessary 
        fileWasClosed = self.fd is None or not self.fd.isopen
        if fileWasClosed:
            if not self.overwrite and os.path.exists(self.filename): nxfilemode = 'rw'
            import nxs
            self.fd = nxs.open(self.filename, nxfilemode)
        #write the data
        self._createBranch(nxpath)
        try:
            self._writeData(name, value, dtype)
        except ValueError, e:
            msg = "Error writing %s. Reason: %s" % (name, str(e))
            self.warning(msg)
            self.macro.warning(msg)
        #leave the file as it was
        if fileWasClosed:
            self.fd.close()
