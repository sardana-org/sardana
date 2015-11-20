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

__all__ = ["NXxas_FileRecorder"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.scan.recorder import BaseNEXUS_FileRecorder

class NXxas_FileRecorder(BaseNEXUS_FileRecorder):
    """saves data to a nexus file that follows the NXsas application definition
    
        """
        
    def __init__(self, filename=None, macro=None, overwrite=False, **pars):
        BaseNEXUS_FileRecorder.__init__(self, filename=filename, macro=macro, overwrite=overwrite, **pars)
        
        
    def _startRecordList(self, recordlist):
        nxs = self.nxs
        if self.filename is None:
            return
        
        #get the recordlist environment
        self.currentlist = recordlist
        env = self.currentlist.getEnviron()
        
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
        
        
        serialno = env["serialno"]
        nxfilemode = self.getFormat()
        if not self.overwrite and os.path.exists(self.filename): nxfilemode='rw'               
        
        self.debug("starting new recording %d on file %s", serialno, self.filename)
        
        #create an nxentry and write it to file
        self.nxentry = nxs.NXentry(name= "entry%d" % serialno)
        self.nxentry.save(self.filename, format=nxfilemode)

        #add fields to nxentry
        import sardana.release
        program_name = "%s (%s)" % (sardana.release.name, self.__class__.__name__)
        self.nxentry.insert(nxs.NXfield(name='start_time', value=env['starttime'].isoformat()))
        self.nxentry.insert(nxs.NXfield(name='title', value=env['title']))
        self.nxentry.insert(nxs.NXfield(name='definition', value='NXxas'))
        self.nxentry.insert(nxs.NXfield(name='epoch', value=time.mktime(env['starttime'].timetuple())))
        self.nxentry.insert(nxs.NXfield(name='program_name', value=program_name, attrs={'version':sardana.release.version}))
        self.nxentry.insert(nxs.NXfield(name='entry_identifier', value=env['serialno']))
                
        #add the "measurement" group (a NXcollection containing all counters from the mntgrp for convenience) 
        measurement = nxs.NXcollection(name='measurement')
        self.ddfieldsDict = {}
        for dd in self.datadesc:
            field = NXfield_comp(name=dd.label,
                                 dtype=dd.dtype,
                                 shape=[nxs.UNLIMITED] + list(dd.shape),
                                 nxslab_dims=[1] + list(dd.shape)
                                 )
            if hasattr(dd,'data_units'):
                field.attrs['units'] = dd.data_units
            measurement.insert(field)
            #create a dict of fields in the datadesc for easier access later on
            self.ddfieldsDict[dd.label] = field
        
        self.nxentry.insert(measurement)
        
        #user group
        nxuser = nxs.NXuser()
        self.nxentry.insert(nxuser)
        nxuser['name'] = env['user']

        #sample group
        nxsample = nxs.NXsample()
        self.nxentry.insert(nxsample)
        nxsample['name'] = env['SampleInfo'].get('name','Unknown')
        
        #monitor group
        scan_acq_time = env.get('integ_time')
        scan_monitor_mode = scan_acq_time>1 and 'timer' or 'monitor'
        nxmonitor = nxs.NXmonitor(mode=scan_monitor_mode,
                        preset=scan_acq_time)
        self.nxentry.insert(nxmonitor)
        monitor_data = self.ddfieldsDict[self.sanitizeName(env['monitor'])] #to be linked later on
        
        #instrument group
        nxinstrument = nxs.NXinstrument()
        self.nxentry.insert(nxinstrument)
        
        #monochromator  group
        nxmonochromator = nxs.NXmonochromator()
        nxinstrument.insert(nxmonochromator)
        energy_data = self.ddfieldsDict[self.sanitizeName(env['monochromator'])] #to be linked later on
        
        #incoming_beam  group
        nxincoming_beam = nxs.NXdetector(name='incoming_beam')
        nxinstrument.insert(nxincoming_beam)
        incbeam_data = self.ddfieldsDict[self.sanitizeName(env['incbeam'])] #to be linked later on
        
        #absorbed_beam  group
        nxabsorbed_beam = nxs.NXdetector(name='absorbed_beam')
        nxinstrument.insert(nxabsorbed_beam)
        absbeam_data = self.ddfieldsDict[self.sanitizeName(env['absbeam'])] #to be linked later on
        absbeam_data.attrs['signal'] = '1'
        absbeam_data.attrs['axes'] = 'energy'
        
        #source group
        nxsource = nxs.NXsource()
        nxinstrument.insert(nxsource) 
        nxinstrument['source']['name'] = env.get('SourceInfo',{}).get('name','Unknown')
        nxinstrument['source']['type'] = env.get('SourceInfo',{}).get('type','Unknown')
        nxinstrument['source']['probe'] = env.get('SourceInfo',{}).get('x-ray','Unknown')
        
        #data group
        nxdata = nxs.NXdata()
        self.nxentry.insert(nxdata)
        
        
        #@todo create the PreScanSnapshot
        #self._createPreScanSnapshot(env)   
        
        #write everything to file
        self.nxentry.write() 
        
        #@todo: do this with the PyTree api instead(how to do named links with the PyTree API????)
        self._nxln(monitor_data, nxmonitor, name='data')
        self._nxln(incbeam_data, nxincoming_beam, name='data')
        self._nxln(absbeam_data, nxabsorbed_beam, name='data')
        self._nxln(energy_data, nxmonochromator, name='energy')
        self._nxln(energy_data, nxdata, name='energy')
        self._nxln(absbeam_data, nxdata, name='absorbed_beam')
                
        self.nxentry.nxfile.flush()
        
    
    def _writeRecord(self, record):
        # most used variables in the loop
        fd, debug, warning = self.nxentry.nxfile, self.debug, self.warning
        nparray, npshape = numpy.array, numpy.shape
        rec_data, rec_nb = record.data, record.recordno
                
        for dd in self.datadesc:
            if record.data.has_key( dd.name ):
                data = rec_data[dd.name]
                field = self.ddfieldsDict[dd.label]
                
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
                    field.put(data, slab_offset, shape)
                    field.write()
                except:
                    warning("Could not write <%s> with shape %s", data, shape)
                    raise
            else:
                debug("missing data for label '%s'", dd.label)
        self.nxentry.nxfile.flush()


    def _endRecordList(self, recordlist):
        env=self.currentlist.getEnviron()
        self.nxentry.insert(nxs.NXfield(name='end_time', value=env['endtime'].isoformat()))
        #self._populateInstrumentInfo()
        #self._createNXData()
        self.nxentry.write()
        self.nxentry.nxfile.flush()
        self.debug("Finishing recording %d on file %s:", env['serialno'], self.filename)
        return
        


#===============================================================================
# BEGIN: THIS BLOCK SHOULD BE REMOVED IF NEXUS ACCEPTS THE PATCH TO NXfield
#===============================================================================
try:
    from nxs import NXfield #needs Nexus v>=4.3
    from nxs import napi, NeXusError
    
    class NXfield_comp(NXfield):
        
        #NOTE: THE CONSTRUCTOR IS OPTIONAL. IF NOT IMPLEMENTED, WE CAN STILL USE THE nxslab_dims PROPERTY
        def __init__(self, value=None, name='field', dtype=None, shape=(), group=None,
                     attrs={}, nxslab_dims=None, **attr):
            NXfield.__init__(self, value=value, name=name, dtype=dtype, shape=shape, group=group,
                     attrs=attrs, **attr)
            self._slab_dims = nxslab_dims
            
        def write(self):
            """
            Write the NXfield, including attributes, to the NeXus file.
            """
            if self.nxfile:
                if self.nxfile.mode == napi.ACC_READ:
                    raise NeXusError("NeXus file is readonly")
                if not self.infile:
                    shape = self.shape
                    if shape == (): shape = (1,)
                    with self.nxgroup as path:
                        if self.nxslab_dims is not None:
                        #compress
                            path.compmakedata(self.nxname, self.dtype, shape, 'lzw', 
                                              self.nxslab_dims)
                        else:
                        # Don't use compression
                            path.makedata(self.nxname, self.dtype, shape)
                    self._infile = True
                if not self.saved:            
                    with self as path:
                        path._writeattrs(self.attrs)
                        value = self.nxdata
                        if value is not None:
                            path.putdata(value)
                    self._saved = True
            else:
                raise IOError("Data is not attached to a file")
        
        def _getnxslabdims(self):
            try:
                return self._nxslab_dims
            except:
                slab_dims = None
            #even if slab_dims have not been set, check if the dataset is large 
            shape = self.shape or (1,)
            if numpy.prod(shape) > 10000:
                slab_dims = numpy.ones(len(shape),'i')
                slab_dims[-1] = min(shape[-1], 100000)
            return slab_dims
        
        def _setnxslabdims(self, slab_dims):
            self._nxslab_dims = slab_dims
        
        nxslab_dims = property(_getnxslabdims,_setnxslabdims,doc="Slab (a.k.a. chunk) dimensions for compression")
except:
    pass #NXxas_FileRecorder won't be usable


#==============================================================================
# END: THE ABOVE BLOCK SHOULD BE REMOVED IF NEXUS ACCEPTS THE PATCH TO NXfield
#==============================================================================
