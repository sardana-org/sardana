
.. _sardana-diffractometer:

==============
Diffractometer
==============

Sardana implements a full control of different types of diffractometers.
The implementation is completely done inside a controller of the type
PseudoMotor. It requires the hkl library developed by Frederic Picca and
available as Debian package
(https://packages.debian.org/source/sid/science/hkl). The use of the library
is exclusively done inside of the controller code, so the hkl binding is only
required if a diffractometer controller is going to be created.

.. note ::
  To use the HklPseudoMotorController you need to install the following Debian
  packages: ``libhkl5`` and ``gir1.2-hkl-5.0``.

The Tango device created inside of the Pool for the diffractometer
controller contains all the commands/attributes for setting the diffractometer,
the movements are done using the real (in real space) and the pseudo (in
reciprocal space) motor devices associated with this controller.

The diffractometer Sardana controller library is called HklPseudoMotorController.
It contains several controller classes depending on the number of real and pseudo
motors needed for each kind of diffractometer. All of them are based on a basic
diffractometer class where the real implementation is done.
Each class cover several diffractometer geometries. A class
property, DiffractometerType, is created for setting the corresponding geometry.
The class properties appear as Tango Device Properties of the device corresponding
to this controller in the Pool. The value of the class properties has to be
assigned when the instance of the diffractometer controller is generated in the Pool.
It is fixed for each diffractometer controller, it can not be changed during
running time.

Up to now the following diffractometer classes are implemented:

::

  Diffrac6C (possible DiffractometerType values: "PETRA3 P09 EH2")
  - motor roles: mu, omega, chi, phi, delta, gamma
  - pseudomotor roles: h, k, l

  DiffracE6C (possible DiffractometerType values: "E6C", "SOLEIL SIXS MED2+2")
  - motor roles: mu, omega, chi, phi, gamma, delta
  - pseudomotor roles: h, k, l, psi, q, alpha, qper, qpar

   DiffracE4C (possible DiffractometerType values: "E4CV", "E4CH", "SOLEIL MARS")
   - motor roles: omega, chi, phi, gamma, tth
   - pseudomotor roles: h, k, l, psi, q
 
   Diffrac4Cp23 (possible DiffractometerType values: "PETRA3 P23 4C")
   - motor roles: omega_t, mu, gamma, delta
   - pseudomotor roles: h, k, l, q, alpha, qper, qpar, tth2, alpha_tth2,
     incidence, emergence

In order to have the diffractometer in Sardana one has to create a PseudoMotor
controller of any of the above classes, this will generate the controller
device, for setting the diffractometer, and the pseudo motor devices, for
the reciprocal space movements. The real motors have to be included as motors
in Sardana, like the motors associated to any other PseudoMotor.

Example::

  defctrl DiffracE6C e6cctrl mu=mot01 omega=mot02 chi=mot03 phi=mot04 \
    gamma=mot05 delta=mot06 h=e6ch k=e6ck l=e6cl psi=e6cpsi q=e6cq \
    alpha=e6calpha qper=e6cqper1 qpar=e6cqpar DiffractometerType E6C

The command above creates the devices corresponding to a diffractometer with E6C
geometry, where ``motXX`` are the names of the Pool devices
associated to each real motor (already existing Motors in Sardana),
``e6cctrl`` is an arbitrary name given to the controller,
and ``e6ch``, ``e6ck`` , ``e6cl``, ``e6cpsi``, ``e6cq``, ``e6calpha``, ``e6cqper1``
and ``e6cqpar`` are the arbitrary names given to the motors in reciprocal space
(PseudoMotors in Sardana, created by this call).

The diffractometer controller device contains as attributes (since it is not
possible add extra commands to the controllers) all the commands and settings for
the diffractometer control. The hkl library needs the parameters to be set in
a given order for being inizialized correctly, for that reason the attribute
values are not stored in the tango database. The best practise is to save the
parameters in a file and load it when startup. Example of a startup file:

::

  Created at 2018-05-28 01:50

  DiffractometerType E6C

  Crystal    srru2o6

  Wavelength 4.36871881607

  A 5.97947283834 B 5.97062576634 C 17.0006259383
  Alpha 90.0 Beta 90.0 Gamma 120.0

  R0 0 0.0 0.0 3.0 0 1 0.0 23.983725 109.768125 286.38645 -1.52587888991e-08 45.344725
  R1 1 1.0 0.0 4.0 0 1 0.0 43.03545 70.0 286.38645 -1.52587888991e-08 83.409275

  Engine hkl

  Mode constant_phi_vertical

  PsiRef not available in current engine mode

  AutoEnergyUpdate 0

  U00 -1.092 U01 -0.250 U02 0.122 
  U10 0.410 U11 0.180 U12 0.348 
  U20 0.332 U21 1.176 U22 -0.027 

  Ux -94.4630713237 Uy 19.3202405308 Uz -162.577336525

  SaveDirectory /home/p09user/crystals

The configuration files can be created by the diffractometer controller by
calling the attribute SaveCrystal. They are loaded by the attribute LoadCrystal.
If nothing is loaded the diffractometer will be inizialized with Sample set to
'default crystal', lattice, wavelenth and geometry set to the corresponding
hkl library default values (according to the geometry) and engine set to 'hkl'.

The wavelength used for the diffractometer can be automatically updated setting
the attribute AutoEnergyUpdate to 1 and the name of the Tango Device controlling
the beam energy in the attribute EnergyDevice. The energy is read from the
attribute Position of the EnergyDevice device, in eV, every time motor or
pseudomotor positions are read.

Sardana provides :ref:`standard macros for controlling the diffractometer <sardana-diffractometer-macros>`.
They need the name of the diffractometer controller device in the Pool to be set
in the macroserver environment variable :ref:`DiffracDevice<diffracdevice>`.
If the Psi angle (azimuth) will be used, the environment variable Psi has to
be set, with the name corresponding PseudoMotor Pool device.

Running the macro :class:`~sardana.macroserver.macros.demo.sar_demo_hkl` creates
a simulated diffractometer in Sardana.

The diffractometer can be controlled from spock used the implemented dedicated macros,
as described in the :ref:`catalog of macros<sardana-standard-macro-catalog>`.
