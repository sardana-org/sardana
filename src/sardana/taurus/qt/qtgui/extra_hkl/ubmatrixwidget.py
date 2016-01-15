#!/usr/bin/env python

# Code implementation generated from reading ui file 'ubmatrixwidget.ui'
#
# Created: Tue Jul 23 12:21:28 2013 
#      by: Taurus UI code generator 3.0.1
#
# WARNING! All changes made in this file will be lost!

__docformat__ = 'restructuredtext'

import sys
import PyQt4.Qt as Qt
from ui_ubmatrixwidget import Ui_ubmatrix
from taurus.qt.qtgui.container import TaurusWidget
from reflectionslist import ReflectionsList
from reflectionseditor import ReflectionsEditor
from taurus.qt.qtgui.base import TaurusBaseWidget

from PyQt4 import QtCore, QtGui

from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.input import TaurusValueLineEdit
import taurus.core

import taurus.core.util.argparse
import taurus.qt.qtgui.application


class PrivateComboBox(Qt.QComboBox, TaurusBaseWidget):
    """ComboBox"""
    
    def __init__(self, parent=None):
        name = self.__class__.__name__
        self.call__init__wo_kw(Qt.QComboBox, parent)
        self.call__init__(TaurusBaseWidget, name)
        self.setSizeAdjustPolicy(Qt.QComboBox.AdjustToContentsOnFirstShow)
        self.setToolTip("Choose an item ...")
        QtCore.QMetaObject.connectSlotsByName(self) 
       
    def loadItems(self, items):
        self.clear()
        self.addItems(items)


class UBMatrixBase(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        
        self._ui = Ui_ubmatrix()
        self._ui.setupUi(self)
        self.connect(self._ui.UpdateButton, Qt.SIGNAL("clicked()"), self.update_values)
        self.connect(self._ui.ComputeUButton, Qt.SIGNAL("clicked()"), self.compute_u)
        self.connect(self._ui.ReflectionsListButton, Qt.SIGNAL("clicked()"), self.reflections_list_window)
        self.connect(self._ui.EditReflectionsButton, Qt.SIGNAL("clicked()"), self.edit_reflections_window)
        self.connect(self._ui.AffineButton, Qt.SIGNAL("clicked()"), self.affine)
        self.connect(self._ui.AddCrystalButton, Qt.SIGNAL("clicked()"), self.add_select_crystal)
#        self.connect(self._ui.alattice_value, Qt.SIGNAL("textEdited()"), self.on_alattice_value_textEdited) 
#       Funciona con puro QEditValue pero no con TaurusQEdit ...

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'ubmatrix'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret
        
    def setModel(self,model):

        self.model = model

        if model !=  None:
            self.device = taurus.Device(model)

        self.update_values()

        uxmodel = model + "/ux" 
        self._ui.taurusuxvalue.setModel(uxmodel)
        self._ui.taurusuxeditvalue.setModel(uxmodel)
        uymodel = model + "/uy" 
        self._ui.taurusuyvalue.setModel(uymodel)
        self._ui.taurusuyeditvalue.setModel(uymodel)
        uzmodel = model + "/uz" 
        self._ui.taurusuzvalue.setModel(uzmodel) 
        self._ui.taurusuzeditvalue.setModel(uzmodel)
        amodel = model + "/a"
        self._ui.taurusalatticevalue.setModel(amodel) 
        self._ui.taurusalatticeeditvalue.setModel(amodel)
        bmodel = model + "/b"
        self._ui.taurusblatticevalue.setModel(bmodel) 
        self._ui.taurusblatticeeditvalue.setModel(bmodel)
        cmodel = model + "/c"
        self._ui.taurusclatticevalue.setModel(cmodel) 
        self._ui.taurusclatticeeditvalue.setModel(cmodel)
        alphamodel = model + "/alpha"
        self._ui.taurusalphalatticevalue.setModel(alphamodel)
        self._ui.taurusalphalatticeeditvalue.setModel(alphamodel)
        betamodel = model + "/beta"
        self._ui.taurusbetalatticevalue.setModel(betamodel)
        self._ui.taurusbetalatticeeditvalue.setModel(betamodel)
        gammamodel = model + "/gamma"
        self._ui.taurusgammalatticevalue.setModel(gammamodel)
        self._ui.taurusgammalatticeeditvalue.setModel(gammamodel)
        psirefhmodel = model + "/psirefh"
        self._ui.taurusvalue_psirefh.setModel(psirefhmodel)
        self._ui.tauruseditvalue_psirefh.setModel(psirefhmodel)
        psirefkmodel = model + "/psirefk"
        self._ui.taurusvalue_psirefk.setModel(psirefkmodel)
        self._ui.tauruseditvalue_psirefk.setModel(psirefkmodel)
        psireflmodel = model + "/psirefl"
        self._ui.taurusvalue_psirefl.setModel(psireflmodel)
        self._ui.tauruseditvalue_psirefl.setModel(psireflmodel) 
        wavelengthmodel = model + "/wavelength"
        self._ui.tauruswavelengthvalue.setModel(wavelengthmodel)          

        # Set model to engine and modes
        
        enginemodel = model + '/engine'
        self._ui.taurusLabelEngine.setModel(enginemodel)
    
        self.enginescombobox = PrivateComboBox(self)
        self.enginescombobox.setGeometry(QtCore.QRect(130, 460, 221, 27))
        self.enginescombobox.setObjectName("engineslist")  
        
        self.enginescombobox.loadItems(self.device.enginelist)
        
        self.connect(self.enginescombobox,Qt.SIGNAL("currentIndexChanged(QString)"), self.onEngineChanged)
        


        enginemodemodel = model + '/enginemode'
        self._ui.taurusLabelEngineMode.setModel(enginemodemodel)
        
        self.enginemodescombobox = PrivateComboBox(self)
        self.enginemodescombobox.setGeometry(QtCore.QRect(130, 500, 221, 27))
        self.enginemodescombobox.setObjectName("enginemodeslist")  
        
        self.enginemodescombobox.loadItems(self.device.enginemodelist)
        
        self.connect(self.enginemodescombobox,Qt.SIGNAL("currentIndexChanged(QString)"), self.onModeChanged)
        
        # Set model to crystal

        crystalmodel = model + '/crystal'
        self._ui.taurusLabelCrystal.setModel(crystalmodel)

        self.crystalscombobox = PrivateComboBox(self)
        self.crystalscombobox.setGeometry(QtCore.QRect(130, 540, 221, 27))
        self.crystalscombobox.setObjectName("crystallist")  
        
        self.crystalscombobox.loadItems(self.device.crystallist)
        
        self.connect(self.crystalscombobox,Qt.SIGNAL("currentIndexChanged(QString)"), self.onCrystalChanged)

              
    def onEngineChanged(self, enginename):
        self.device.write_attribute("engine", str(enginename))

    def onModeChanged(self, modename):
        self.device.write_attribute("enginemode", str(modename))
        

    def onCrystalChanged(self, crystalname):
        self.device.write_attribute("crystal", str(crystalname))
        

#    def on_alatticeeditvalue_textEdited(self, text):
#        print "Funciona"
#        print text       
       # textEdited
                  
    def update_values(self):
        ub_values = self.device.ubmatrix
        self._ui.taurusub11value.setValue(ub_values[0][0])
        self._ui.taurusub12value.setValue(ub_values[0][1])
        self._ui.taurusub13value.setValue(ub_values[0][2])
        self._ui.taurusub21value.setValue(ub_values[1][0])
        self._ui.taurusub22value.setValue(ub_values[1][1])
        self._ui.taurusub23value.setValue(ub_values[1][2])
        self._ui.taurusub31value.setValue(ub_values[2][0])
        self._ui.taurusub32value.setValue(ub_values[2][1])
        self._ui.taurusub33value.setValue(ub_values[2][2]) 

    def compute_u(self):
        index = [0,1]
        
        self.device.write_attribute("computeu", index)

    def reflections_list_window(self):

        reflections = self.device.reflectionlist
            
        nb_ref = 0
        xindex = 20
        xh = 70
        xk = 150
        xl = 230
        xrelevance = 330
        xaffinement = 380
        xangle1 = 430
        xangle2 = 510
        xangle3 = 590
        xangle4 = 670
        xangle5 = 750
        xangle6 = 830
        yhkl = 100
        w = ReflectionsList()

        self.taurusValueIndex = []
        self.taurusValueH = []
        self.taurusValueK = []
        self.taurusValueL = []
        self.taurusValueRelevance = []
        self.taurusValueAffinement = []
        self.taurusValueAngle1 = []
        self.taurusValueAngle2 = []
        self.taurusValueAngle3 = []
        self.taurusValueAngle4 = []
        self.taurusValueAngle5 = []
        self.taurusValueAngle6 = []
    
        if reflections != None:
            for ref in reflections:
                if nb_ref == 0:
                    self.rl_label1_7 = QtGui.QLabel(w)
                    self.rl_label1_7.setGeometry(QtCore.QRect(xangle1 + 20, 70, 51, 20))
                    self.rl_label1_7.setObjectName("rl_label1_7")
                #               self.testlabel.setLayoutDirection(QtCore.Qt.RightToLeft)
                    self.rl_label1_8 = QtGui.QLabel(w)
                    self.rl_label1_8.setGeometry(QtCore.QRect(xangle2 + 20, 70, 41, 20))
                    self.rl_label1_8.setObjectName("rl_label1_8")
                #               self.testlabel.setLayoutDirection(QtCore.Qt.RightToLeft)
                    self.rl_label1_9 = QtGui.QLabel(w)
                    self.rl_label1_9.setGeometry(QtCore.QRect(xangle3 + 20, 70, 41, 20))
                    self.rl_label1_9.setObjectName("rl_label1_9")
                    self.rl_label1_10 = QtGui.QLabel(w)
                    self.rl_label1_10.setGeometry(QtCore.QRect(xangle4 + 20, 70, 41, 20))
                    self.rl_label1_10.setObjectName("rl_label1_10")     
                    try:
                        self.angle_names = self.device.motorroles
                    except: # Only for compatibility
                        if self.nb_motors == 4:
                            self.angles_names.append("omega")
                            self.angles_names.append("chi")
                            self.angles_names.append("phi")
                            self.angles_names.append("theta")
                        elif self.nb_motors == 6:
                            self.angles_names.append("mu")
                            self.angles_names.append("th")
                            self.angles_names.append("chi")
                            self.angles_names.append("phi")
                            self.angles_names.append("gamma")
                            self.angles_names.append("delta")
                # 4circles diffractometer
                    if len(ref) == 10:
                        self.rl_label1_7.setText(QtGui.QApplication.translate("Form", self.angle_names[0], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_8.setText(QtGui.QApplication.translate("Form", self.angle_names[1], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_9.setText(QtGui.QApplication.translate("Form", self.angle_names[2], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_10.setText(QtGui.QApplication.translate("Form", self.angle_names[3], None, QtGui.QApplication.UnicodeUTF8))
                # 6 circles diffractometer
                    elif len(ref) == 12:
                        self.rl_label1_11 = QtGui.QLabel(w)
                        self.rl_label1_11.setGeometry(QtCore.QRect(xangle5 + 20, 70, 41, 20))
                        self.rl_label1_11.setObjectName("rl_label1_11")
                        self.rl_label1_12 = QtGui.QLabel(w)
                        self.rl_label1_12.setGeometry(QtCore.QRect(xangle6 + 20, 70, 41, 20))
                        self.rl_label1_12.setObjectName("rl_label1_12")
                        self.rl_label1_7.setText(QtGui.QApplication.translate("Form", self.angle_names[0], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_8.setText(QtGui.QApplication.translate("Form", self.angle_names[1], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_9.setText(QtGui.QApplication.translate("Form", self.angle_names[2], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_10.setText(QtGui.QApplication.translate("Form", self.angle_names[3], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_11.setText(QtGui.QApplication.translate("Form", self.angle_names[4], None, QtGui.QApplication.UnicodeUTF8))
                        self.rl_label1_12.setText(QtGui.QApplication.translate("Form", self.angle_names[5], None, QtGui.QApplication.UnicodeUTF8))
                    

                self.taurusValueIndex.append(TaurusValueLineEdit(w))
                self.taurusValueIndex[nb_ref].setGeometry(QtCore.QRect(xindex, 100 + 30*(nb_ref), 41, 27))
                self.taurusValueIndex[nb_ref].setReadOnly(True)
                indexname = "taurusValueIndex" + str(nb_ref+2) 
                self.taurusValueIndex[nb_ref].setObjectName(indexname)
                self.taurusValueIndex[nb_ref].setValue(int(ref[0]))

                self.taurusValueH.append(TaurusValueLineEdit(w))
                self.taurusValueH[nb_ref].setGeometry(QtCore.QRect(xh, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueH[nb_ref].setReadOnly(True)
                hname = "taurusValueH" + str(nb_ref+2) 
                self.taurusValueH[nb_ref].setObjectName(hname)
                self.taurusValueH[nb_ref].setValue("%10.4f" % ref[1])
                    
                self.taurusValueK.append(TaurusValueLineEdit(w))
                self.taurusValueK[nb_ref].setGeometry(QtCore.QRect(xk, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueK[nb_ref].setReadOnly(True)
                kname = "taurusValueK" + str(nb_ref+2) 
                self.taurusValueK[nb_ref].setObjectName(kname)
                self.taurusValueK[nb_ref].setValue("%10.4f" % ref[2])

                self.taurusValueL.append(TaurusValueLineEdit(w))
                self.taurusValueL[nb_ref].setGeometry(QtCore.QRect(xl, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueL[nb_ref].setReadOnly(True)
                lname = "taurusValueL" + str(nb_ref+2) 
                self.taurusValueL[nb_ref].setObjectName(lname)
                self.taurusValueL[nb_ref].setValue("%10.4f" % ref[3])

                self.taurusValueRelevance.append(TaurusValueLineEdit(w))
                self.taurusValueRelevance[nb_ref].setGeometry(QtCore.QRect(xrelevance, 100 + 30*(nb_ref), 41, 27))
                self.taurusValueRelevance[nb_ref].setReadOnly(True)
                relevancename = "taurusValueRelevance" + str(nb_ref+2) 
                self.taurusValueRelevance[nb_ref].setObjectName(relevancename)
                self.taurusValueRelevance[nb_ref].setValue(int(ref[4]))
                
                self.taurusValueAffinement.append(TaurusValueLineEdit(w))
                self.taurusValueAffinement[nb_ref].setGeometry(QtCore.QRect(xaffinement, 100 + 30*(nb_ref), 41, 27))
                self.taurusValueAffinement[nb_ref].setReadOnly(True)
                affinementname = "taurusValueAffinement" + str(nb_ref+2) 
                self.taurusValueAffinement[nb_ref].setObjectName(affinementname)
                self.taurusValueAffinement[nb_ref].setValue(int(ref[5]))
                
                self.taurusValueAngle1.append(TaurusValueLineEdit(w))
                self.taurusValueAngle1[nb_ref].setGeometry(QtCore.QRect(xangle1, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueAngle1[nb_ref].setReadOnly(True)
                angle1name = "taurusValueAngle1" + str(nb_ref+2) 
                self.taurusValueAngle1[nb_ref].setObjectName(angle1name)
                self.taurusValueAngle1[nb_ref].setValue("%10.4f" % ref[6])
                
                self.taurusValueAngle2.append(TaurusValueLineEdit(w))
                self.taurusValueAngle2[nb_ref].setGeometry(QtCore.QRect(xangle2, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueAngle2[nb_ref].setReadOnly(True)
                angle2name = "taurusValueAngle2" + str(nb_ref+2) 
                self.taurusValueAngle2[nb_ref].setObjectName(angle2name)
                self.taurusValueAngle2[nb_ref].setValue("%10.4f" % ref[7])

                self.taurusValueAngle3.append(TaurusValueLineEdit(w))
                self.taurusValueAngle3[nb_ref].setGeometry(QtCore.QRect(xangle3, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueAngle3[nb_ref].setReadOnly(True)
                angle3name = "taurusValueAngle3" + str(nb_ref+2) 
                self.taurusValueAngle3[nb_ref].setObjectName(angle3name)
                self.taurusValueAngle3[nb_ref].setValue("%10.4f" % ref[8])
                
                self.taurusValueAngle4.append(TaurusValueLineEdit(w))
                self.taurusValueAngle4[nb_ref].setGeometry(QtCore.QRect(xangle4, 100 + 30*(nb_ref), 81, 27))
                self.taurusValueAngle4[nb_ref].setReadOnly(True)
                angle4name = "taurusValueAngle4" + str(nb_ref+2) 
                self.taurusValueAngle4[nb_ref].setObjectName(angle4name)
                self.taurusValueAngle4[nb_ref].setValue("%10.4f" % ref[9])
            
                if len(ref) == 12:
                    self.taurusValueAngle5.append(TaurusValueLineEdit(w))
                    self.taurusValueAngle5[nb_ref].setGeometry(QtCore.QRect(xangle5, 100 + 30*(nb_ref), 81, 27))
                    self.taurusValueAngle5[nb_ref].setReadOnly(True)
                    angle5name = "taurusValueAngle5" + str(nb_ref+2) 
                    self.taurusValueAngle5[nb_ref].setObjectName(angle5name)
                    self.taurusValueAngle5[nb_ref].setValue("%10.4f" % ref[10])

                    self.taurusValueAngle6.append(TaurusValueLineEdit(w))
                    self.taurusValueAngle6[nb_ref].setGeometry(QtCore.QRect(xangle6, 100 + 30*(nb_ref), 81, 27))
                    self.taurusValueAngle6[nb_ref].setReadOnly(True)
                    angle6name = "taurusValueAngle6" + str(nb_ref+2) 
                    self.taurusValueAngle6[nb_ref].setObjectName(angle6name)
                    self.taurusValueAngle6[nb_ref].setValue("%10.4f" % ref[11])

                nb_ref = nb_ref + 1

            w.resize(930, 100 + nb_ref*50)
  
        else:         
           self.rl_label_nor = QtGui.QLabel(w)
           self.rl_label_nor.setGeometry(QtCore.QRect(xangle1 - 50, 110, 300, 20))
           font = QtGui.QFont()
           font.setPointSize(12)
           font.setWeight(75)
           font.setBold(True)
           self.rl_label_nor.setFont(font)
           self.rl_label_nor.setObjectName("rl_label_nor") 
           self.rl_label_nor.setText(QtGui.QApplication.translate("Form", "NO REFLECTIONS", None, QtGui.QApplication.UnicodeUTF8))
        
        w.show()        
        w.show()


    def edit_reflections_window(self):

        w = ReflectionsEditor()
        w.setModel(self.model)
        
        w.show() 

    def add_select_crystal(self):

        new_crystal = str(self._ui.NewCrystalLineEdit.text())
        self.device.write_attribute("AddCrystal", new_crystal)   
        self.crystalscombobox.loadItems(self.device.crystallist)
        self.device.write_attribute("Crystal", new_crystal)     

    def affine(self):
               
        self.device.write_attribute("affine", 1)

def main(): 
    
    parser = taurus.core.util.argparse.get_taurus_parser()
    parser.usage = "%prog [options] <model>"
#    taurus.qt.qtgui.application.TaurusApplication(cmd_line_parser=parser)

    app = taurus.qt.qtgui.application.TaurusApplication(cmd_line_parser=parser)
    args = app.get_command_line_args()
    if len(args) < 1:
        sys.stderr.write("Need to supply model attribute")
        sys.exit(1)

    w =UBMatrixBase ()
    w.model = args[0]
    w.setModel(w.model)
    w.show()

    sys.exit(app.exec_())

 #   if len(sys.argv)>1: model=sys.argv[1]
 #   else: model = None

 #   app = Qt.QApplication(sys.argv)
 #   w = UBMatrixBase()
 #   w.setModel(model)
 #   w.show()
 #   sys.exit(app.exec_())

if __name__ == "__main__":
    main()
