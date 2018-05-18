##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

"""Examples of macro to execute sequencies in a file"""

from __future__ import print_function

__all__ = ["run_seq"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.macro import Type, Macro
import PyTango
import time

    

class run_seq(Macro):
    param_def = [
        ['seq_file',Type.String,   None, 'Name of the file with the sequency of macros']
        ]
    
    def run(self, seq_file):
        self.output("Running sequency %s", seq_file)

        try:
            seq_path = self.getEnv("SequencyPath") + "/"
        except:
            self.output("Not SequencyPath defined. File searched in MacroServer dir")
            seq_path = ""

        seq_file = seq_path + seq_file
        try:
            f_seq = open(seq_file, 'r')
        except:
            self.output("Enable to read file %s", seq_file)
            return
        
        for macro_info in f_seq:
            self.output("Running macro %s", macro_info)
            self.execMacro(macro_info)
                
