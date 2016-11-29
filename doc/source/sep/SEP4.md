	Title: HKL integration in Sardana
	SEP: 4
	State: ACCEPTED
	Date: 2013-06-28
	Drivers: Teresa Nunez <maria-teresa.nunez-pardo-de-vera@desy.de>
	URL: http://www.sardana-controls.org/sep/?SEP4.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	This SEP describes the integration in Sardana of the HKL library developed
	by Frederic Picca.


Introduction
============

The integration of the HKL library will allow Sardana to control different types of diffractometers. This document describes how this integration is done and the interface for the user.

Status
======

The SEP4 implements the diffractometer control inside of Sardana using the HKL library developed by
Frederic Picca.
This implemention is used for the full control of the diffractometer in one of the Petra beamlines at DESY.

Description of the current implementation
=========================================

The diffractometers are introduced in Sardana as controllers of the type PseudoMotor, for that reason the use of the hkl library binding is exclusively done in the code implementing these diffractometer controllers.

There is a basis diffractometer controller class, implementing the common part of the different types of diffractometers, and several other classes, derived from the basis one, which implement what is specific for each diffractometer type. Up to now the only difference between these several classes is the number of pseudo motor and motor roles requiered: hkl library diffractometer types with the same number of motors and pseudomotors are represented by the same sardana diffractometer controller type.

## Basis Diffractometer Class 

It contains the common code for all the diffractometers.

The initialization of the class set the sample to 'default_crystal', set lattice values to default ones, and creates geometry corresponding to the diffractometer type selected in a class property (see below). The engine is set to 'hkl'.

The functions calc_all_physical and calc_all_pseudos implement the calculation of the positions for real and pseudo axes associated to the diffractometer. This calculations are used for performing the movements. The different engines are taken into account and the calculation of the positions and movements are done according to the selected one.

The following extra properties and attributes are implemented for this class.

### Class properties
The value of the class properties has to be assigned when the instance of the diffractometer controller is generated in the Pool. It is fixed for each diffractometer controller, it can not be changed during running time. The class properties appear as Tango Device Properties of the device corresponding to this controller in the Pool process.

* DiffractometerType: the name of the type of this diffractometers so like it is in the hkl library. This property is used for generating the right geometry and engine and getting the number of axes (real motors) implied.

### Controller attributes
The controller attributes appear as Tango Attributes of the device corresponding to the controller. As controller attributes are implemented all the parameters which characterize the current status of the diffractrometer. Since there is no possibility of adding command to the controller device, also the commands for performing actions, computations, etc. are implemented as attributes. 

* **A**: a parameter of the current lattice.
* **AddCrystal**: add a new sample.
* **AddReflection**: add reflection to current sample.
* **SubstituteReflection**: substitute reflexion with the given index by the given one.
* **AdjustAnglesToReflection**: changes the angles associated to the selected reflection.
* **AffineCrystal**: creates a new sample with '(affine)' attached to the name of the current one and performs the affine. This  affine sample is set as the current one. 
* **Afit**: fit value of the a parameter of the current lattice.
* **Alpha**: alpha parameter of the current lattice.
* **AlphaFit**: fit value of the alpha parameter of the current lattice.
* **AutoEnergyUpdate**: if set to 1 the energy is read from the device set in the attribute EnergyDevice every time the wavelength attribute is read. The readout of the wavelength attribute is done internally every time the pseudomotor positions are recalculated.
* **B**: b parameter of the current lattice. 
* **Beta**: beta parameter of the current lattice.
* **BetaFit**: fit value of the beta parameter of the current lattice.  
* **Bfit**: fit value of the b parameter of the current lattice.
* **C**: c parameter of the current lattice.
* **Cfit**: fit value of the c parameter of the current lattice.
* **ComputeHKL**: compute the hkl values corresponding to the angles set in these attribute.
* **ComputeTrajectoriesSim**: computes the list of trajectories for the current engine and engine mode corresponding to the values of the pseudo axes written in this attribute. The number of arguments has to correspond to the number of pseudo axes for the current engine. The computed trajectories are shown in the TrajectoryList attribute. 
* **ComputeUB**: computes UB matrix using the reflections corresponding to the indexes given as arguments.
* **Crystal**: sample.
* **CrystalList**: list of samples.
* **DeleteCrystal**: delete the crystal given in the argument.
* **EnergyDevice**: name of the Tango device the energy will be read from. The readout of the energy is done every time the wavelength is required if the attribute AutoEnergyUpdate is set to 1. The name of the attribute the energy is read from is Position.
* **Engine**: selected engine. It is taken into account for computing the physical positions corresponding to a movement of a pseudo axis. 
* **EngineList**: list of engines for the diffractometer type corresponding to this controller.
* **EngineMode**: selected mode for the current.
* **EngineModeList**: list of the modes corresponding to the current engine.
* **HKLModeList**: list of the modes corresponding to the hkl engine.
* **HKLPseudoMotorList**: list of the hkl motor names.
* **Gamma**: gamma parameter of the current lattice. 
* **GammaFit**: fit value of the gamma parameter of the current lattice.
* **LoadCrystal**: loads crystal name, wavelength, lattice parameters, reflections 0 and 1, engine mode and psi ref vector (in case available in mode) from ascii file. It also set the SaveDirectory attribute if it is empty. These settings will be loaded from the last loaded file when the Pool is started.
* **LoadReflections**: loads reflections for current crystal from ascii file.
* **LatticeReciprocal**: reads the values of the reciprocal lattice.  
* **ModeParametersNames**: name of the parameters assotiated to the current engine mode (if any).   
* **ModeParametersValues**: get/set the value of the parameters assotiated to the current engine mode (if any).
* **MotorList**: names of the physical motors associated to the diffractometer.
* **MotorRoles**: names of the motor roles corresponding to this diffractometer.
* **PsiRefH**: H coordinate of the psi reference vector, for the modes that it applies. -999 if it does not apply.
* **PsiRefK**: K coordinate of the psi reference vector, for the modes that it applies. -999 if it does not apply.
* **PsiRefL**: L coordinate of the psi reference vector, for the modes that it applies. -999 if it does not apply.
* **ReflectionAngles**: angles (computed and theoretical) between the reflections of the current sample. 
* **ReflectionList**: list of reflections for current sample.  
* **RemoveReflection**: remove reflection with given index.
* **SaveCrystal**: saves current crystal name, wavelength, lattice parameters, first and second reflections, engine mode, ub matrix, u vector, psi reference vector and SaveDirectory attribute to two files: one with the name defaultcrystal.txt and other with the name of the current crystal/sample. The files are saved in the directory written in the attribute SaveDirectory.

Example of a saved file:
```
Created at 2015-01-09 11:32

Crystal    default_crystal

Wavelength 1.54

A 1.5 B 1.5 C 1.5
Alpha 90.0 Beta 90.0 Gamma 90.0

R0 0 1.0 1.0 1.0 0 1 1.0 63.0 4.0 -44.623 10.0 93.192
R1 1 1.0 1.0 1.0 0 1 1.0 63.0 4.0 -44.623 10.0 93.192

Mode constant_phi_vertical

PsiRef not available in current engine mode

U00 4.189 U01 -0.000 U02 -0.000 
U10 0.000 U11 4.189 U12 -0.000 
U20 0.000 U21 0.000 U22 4.189 

Ux 0.0 Uy 0.0 Uz 0.0

SaveDirectory /home/tnunez
```

* **SaveDirectory**: name of the directory where the files with the crystal information will be saved.
* **SaveReflections**: saves reflections from current crystal to ascii file. The value written to this attribute is the path to the file, the name of the file is the name of the sample with the termination .ref. If this file already exists a copy will be created adding to the name the current time in seconds.  
* **SelectedTrajectory**: index of the trajectory you want to take when you perform a movement for a given set of pseudo axes positions.
* **SwapReflections01**: swap primary and secondary reflections.
* **TrajectoryList**: list of trajectories for the current engine and engine mode corresponding to the pseudo axes values written in the ComputeTrajectoriesSim attribute and the engine and engine mode when the calculation was performed. It gives the possibility of checking the trajectories before performing a movement.
* **UBMatrix**: reads current UB matrix values.
* **Ux**: reads/writes current ux value. 
* **Uy**: reads/writes current uy value. 
* **Uz**: reads/writes current uz value. 
* **Wavelength**. 


The controller attributes are by default stored and written at initialization. However we have set most of the attributes to memorized but not written at init. This is due to the fact that for the hkl library it is important
the order in which crystal, reflections, lattice parameters and other geometry settings are set, and this
required order can not be controlled if the attributes are automatically set at init. The best practise is to
 load a saved crystal file after the initialization is done.

## Diffractometer Types 

The different diffractometer types covered by the hkl library have been grouped according to the axes and pseudo axes involved. A controller class has been developed for each of these groups. These classes derive from the basis one and only differs in the defined motor and pseudo motor roles. Creating an instance of any of these controller classes requires to give a value to all the associated motor and pseudo motor roles.
Even if the choose of one of these diffractometer classes is already determined for the type of the diffractometer we are going to use, the property DiffratometerType described in the basis class is still required because several library diffractometer types have the same motors and pseudo motors.

The following diffractometer controller classes are implemented:
```
* Diffrac6C (covers diffractometer type "PETRA3 P09 EH2")
  pseudo_motor_roles = "h", "k", "l"
  motor_roles = "mu", "th", "chi", "phi", "gamma", "delta"
* DiffracE6C (covers diffractometer types "E6C", "SOLEIL SIXS MED2+2") 
  pseudo_motor_roles = "h", "k", "l","psi","q21","q22","qperqpar1","qperpar2"
  motor_roles = "omega", "chi", "phi", "tth"
* DiffracE4C (covers diffractometer types  "E4CV", "E4CH", "SOLEIL MARS")
  pseudo_motor_roles = "h", "k", "l","psi","q"
  motor_roles = "omega", "chi", "phi", "tth"
```
The following diffractometer controller classes were removed from a previous version of the controller, since
they were no supported or tested any more inside the hkl library. We expect, they will be available in the future:
```  
* DiffracK6C (covers diffractometer type "K6C")
  pseudo_motor_roles = "h", "k", "l","psi","q21","q22","qperqpar1","qperpar2","eulerians1", "eulerians2","eulerians3"
  motor_roles = "omega", "chi", "phi", "tth" 
* Diffrac4C (default 4 circles diffractometers)
  pseudo_motor_roles = "h", "k", "l"
  motor_roles = "omega", "chi", "phi", "tth"
* DiffracK4C (covers diffractometer type "K4CV")
  pseudo_motor_roles = "h", "k", "l","psi","q","eulerians1", "eulerians2","eulerians3"
  motor_roles = "omega", "chi", "phi", "tth"  
* Diffrac4CZAXIS (covers diffractometer types "ZAXIS", "SOLEIL SIXS MED1+2")
  pseudo_motor_roles = "h", "k", "l","q21","q22","qperqpar1","qperqpar2"
  motor_roles = "omega", "chi", "phi", "tth"
* Diffrac2C (default 2 circles diffractometers)
  pseudo_motor_roles = "h", "k", "l"
  motor_roles = "omega","tth"  
  ```
  
## Diffractometer GUI

A Graphical User Interface is being developed for controlling the diffractometer.
The GUI is based on PyQt/Taurus and connected to the diffractometer Pool controller device.
Up to now there are three main GUI applications dedicated to hkl scans, diffractometer
alignment and UB matrix/lattice parameters and reflections.

## Diffractometer Macros

A set of macros for controlling the diffractometer and displaying information have been
developed. They try to follow the spec sintax.

## Required HKL Package

The required package containing the hkl calculations is gir1.2-hkl-5.0 and it is
 available for Debian _jessie_  (from backports):

<https://packages.debian.org/jessie-backports/gir1.2-hkl-5.0>

If you want to install this on the _jessie_ version add this line:

`deb http://ftp.debian.org/debian jessie-backports main`

to your sources.list (or add a new file with the ".list" extension to `/etc/apt/sources.list.d/`) You can also find a list of other mirrors at https://www.debian.org/mirror/list

Run `apt-get update`

and then for the python binding

`apt-get source -t jessie-backports gir1.2-hkl-5.0`

You can also install it by rebuilding it on your system.

The steps to do are:

1) add the source of the jessie-backports distribution into  `/etc/apt/sources`:
 
`deb-src http://ftp.debian.org/debian jessie-backports main contrib non-free`

2) `apt-get update`

3) `apt-get build-dep hkl`

4) `cd /tmp && apt-get source -b hkl`

It should build a bunch of .deb files and you could install them with

`dpkg -i *.deb`

To test it:

`python -c "from gi.repository import Hkl"`

Known issues & possible improvements
-------------------------------------

* General
    * Documentation is missing.
    * Current implementaion of the diffractometer controllers is not generic and requires a new controller class per each geometry. Whenever the following Sardana [feature-request](https://github.com/sardana-org/sardana/issues/86) is implemented the diffractometer controllers should take profit of it.
* GUIs
    * As it is now, the hklscan widget "Display Angles" requires all dimensions (H & K & L) to be specified even if one wants to execute less than 3 dimensions scan e.g. to execute the ascan of H axis, the K & L dimensions needs equal the start and the end positions. This could be improved.
    * "ComputeUB" of the ubmatrix widget works only when at least 2 reflexions are defined for the current crystal. If one tries to execute it and this requirement is not fulfield, the widget does silently ignore the requets. It could inform the user about the missing reflexions.
    * diffractometeralignment widget parses the \_diff_scan output. The more generic way of executing scan and finding a peak in order to send the motor there should be found.
* Controller
    * I see that the controller defines many MemorizedNoInit attribute but the memorized values are never extracted from the database (no calls to get_attribute_memorized_value). We should decide whether we need any of the attributes as memorize and make a proper use of them.
    * Many of the attributes are only foreseen to write (they are substituting commands). I think it would be a good idea to raise exceptions when someone tries to read them, explaining that they are not foreseen to read.
    * Attributes' formats could be better documented - now there are comments in the code, which could be transformed into the sphinx documentation of the methods or even to the attribute's description in the attribute's definition.
    * There are some places in the code that the abnormal conditions are silently ignored, or just logged, instead of raising descriptive exceptions e.g. when write value of the attribute does not follow the expected syntax, etc. I suggest to use exceptions.
    * All the fit attributes (e.g. AFit or GammaFit) should change its type to bool.
    * There other already existing TODOs in the code.
* Macros:
    * use taurus instead of PyTango API e.g. read_attribute, write_attribute. The hkl macro module is full of PyTango centric calls.
    * use explicit getters to obtain Sardana elements (controller - getController, pseudomotor - getPseudoMotor, ...) instead of using getDevice. However this getter seems to accept only the elements names and not the full names.
    * it should not be necessary to implement on_stop methods in the macros in order to stop the moveables. Macro API should provide this kind of emergency stop (if the moveables are correctly reserved with the getMotion method) in case of aborting a macro.
    * br and ubr macros require refactoring in order to use events instead of polling to obtain the position updates. See umv macro as an example.
    * br and ubr macro parameters: H, K, L should be of type float and not string
    * luppsi is not tested
    
Links to more details and discussions
-------------------------------------

Some discussions about integration of this sep in sardana develop branch:
<https://sourceforge.net/p/sardana/mailman/sardana-devel/thread/5698B4B5.10903%40cells.es/#msg34768418>

 License
-------

The following copyright statement and license apply to SEP4 (this
document).

Copyright (c) 2013  Teresa Nunez

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


Changes
-------

* 2013-06-28:
  [tere29](https://sourceforge.net/u/tere29/) Implementation started in sep4 branch

* 2016-01-21:
   State changed from DRAFT to CANDIDATE

* 2016-04-07:
   State changed from CANDIDATE to ACCEPTED

* 2016-11-18 by zreszela:
    Minor change to add info how to install HKL library from jessie-backports

* 2016-11-29: 
 [mrosanes](https://github.com/sagiss) Migrate SEP4 from SF wiki to independent file, modify URL, fix formatting and correct links.
