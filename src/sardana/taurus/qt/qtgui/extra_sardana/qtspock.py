#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2020 DESY
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

"""A RichJupyterWidget that loads a spock profile.

.. note::
        The `qtspock` module has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.
"""
import sys
import pickle
import ast

import traitlets
from IPython.core.profiledir import ProfileDirError, ProfileDir

from taurus.external.qt import Qt
from taurus import info, error

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager

from taurus.qt.qtgui.base import TaurusBaseWidget
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.resource import getThemeIcon

from sardana import release
from sardana.spock.ipython_01_00.genutils import get_profile_metadata, \
    get_ipython_dir, from_name_to_tango, get_macroserver_for_door
from sardana.taurus.qt.qtgui.extra_macroexecutor import \
    TaurusMacroConfigurationDialog


def get_spock_profile_dir(profile):
    """Return the path to the profile with the given name."""
    try:
        profile_dir = ProfileDir.find_profile_dir_by_name(
            get_ipython_dir(), profile)
    except ProfileDirError:
        return None
    return profile_dir.location


def check_spock_profile(profile):
    """Check if the profile exists and has the correct value"""
    profile_dir = get_spock_profile_dir(profile)
    if profile_dir:
        profile_version_str, door_name = get_profile_metadata(profile_dir)
        if profile_version_str == release.version:
            return True
    return False


class SpockKernelManager(QtKernelManager):
    """
    A kernel manager that checks the spock profile before starting a kernel.

    .. note::
        The `SpockKernelManager` class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.

    If the check fails, i.e., the profile does not exist or has a different
    version, an ipython kernel without spock functionality is started instead
    and the attribute `valid_spock_profile` is set to `False`.
    """
    kernel_about_to_launch = Qt.pyqtSignal()

    def _launch_kernel(self, kernel_cmd, **kw):
        try:
            profile = kernel_cmd[kernel_cmd.index("--profile") + 1]
        except ValueError:
            self.is_valid_spock_profile = False
        else:
            if check_spock_profile(profile):
                self.is_valid_spock_profile = True
            else:
                index = kernel_cmd.index("--profile")
                del kernel_cmd[index]
                del kernel_cmd[index]
                for arg in kernel_cmd[:]:
                    if arg.startswith("--Spock"):
                        kernel_cmd.remove(arg)
                self.is_valid_spock_profile = False
                error("Checking spock profile failed.")
        info('Starting kernel...')
        self.kernel_about_to_launch.emit()
        return super()._launch_kernel(kernel_cmd, **kw)


class QtSpockWidget(RichJupyterWidget, TaurusBaseWidget):
    """A RichJupyterWidget that starts a kernel with a spock profile.

    .. note::
        The `QtSpockWidget` class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.

    It is important to call `shutdown_kernel` to gracefully clean up the
    started subprocesses.

    Useful methods of the base class include execute, interrupt_kernel,
    restart_kernel, and clear.

    :param profile:
        The name of the spock profile to use. The default is 'spockdoor'.
    :type profile: str
    :param kernel:
        The name of the kernel to use. The default is 'python3'.
    :type  kernel: str
    :param use_model_from_profile:
        If true, the door name is taken from the spock profile, otherwise it
        has to be set via setModel.
    :type use_model_from_profile: bool
    :param kwargs:
        All remaining keywords are passed to the RichJupyterWidget base class

    Examples::

        from taurus.external.qt import Qt
        from sardana.taurus.qt.qtgui.extra_sardana.qtspock import QtSpockWidget
        app = Qt.QApplication(["qtspock"])
        widget = QtSpockWidget(use_model_from_profile=True)
        widget.show()
        widget.start_kernel()
        app.aboutToQuit.connect(widget.shutdown_kernel)
        app.exec_()
    """
    def __init__(
            self,
            parent=None,
            profile='spockdoor',
            use_model_from_profile=False,
            extensions=None,
            kernel='python3',
            **kw):
        RichJupyterWidget.__init__(self, parent=parent, **kw)
        TaurusBaseWidget.__init__(self)
        self.setObjectName(self.__class__.__name__)
        self.setModelInConfig(True)

        self._profile = profile
        self.use_model_from_profile = use_model_from_profile

        if extensions is None:
            extensions = []
        extensions.insert(
            0, "sardana.taurus.qt.qtgui.extra_sardana.qtspock_ext")

        self._extensions = extensions
        self._kernel_name = kernel

        self._macro_server_name = None
        self._macro_server_alias = None
        self._door_name = None
        self._door_alias = None
        self._config_passed_as_extra_arguments = False

        self.append_stream("Waiting for kernel to start")

        self.kernel_manager = SpockKernelManager(kernel_name=kernel)
        self.kernel_manager.kernel_about_to_launch.connect(
            self._handle_kernel_lauched)

    def start_kernel(self):
        """Start the kernel

        A normal IPython kernel is started if no model is set via `setModel` or
        `use_model_from_profile`.
        """
        if not self.kernel_manager.has_kernel:
            self.kernel_manager.start_kernel(
                extra_arguments=self._extra_arguments())
            kernel_client = self.kernel_manager.client()
            kernel_client.start_channels()
            self.kernel_client = kernel_client

    def _extra_arguments(self):
        extra_arguments = ["--profile", self._profile]
        for ext in self._extensions:
            extra_arguments.extend(["--ext", ext])

        if not self.use_model_from_profile:
            if self._macro_server_name and self._door_name:
                self._config_passed_as_extra_arguments = True
                extra_arguments.append("--Spock.macro_server={}".format(
                    self._macro_server_name))
                extra_arguments.append("--Spock.macro_server_alias={}".format(
                    self._macro_server_alias))
                extra_arguments.append("--Spock.door_name={}".format(
                    self._door_name))
                extra_arguments.append("--Spock.door_alias={}".format(
                    self._door_alias))
            else:
                # Loading the spock profile would use the macro server and door
                # configured there. Instead, use no extra arguments for an
                # ipython kernel without Spock functionality
                extra_arguments = []

        return extra_arguments

    def setModel(self, door):
        """Set a door as the model

        An empty string or None will start a normal IPython kernel without
        spock functionality.
        """
        old_door_name = self._door_name
        old_macroserver_name = self._macro_server_name
        self._set_door_name(door)
        self._set_macro_server_name(door)

        if (self._door_name == old_door_name
                and self._macro_server_name == old_macroserver_name):
            return

        if self.kernel_manager.has_kernel:
            # RichJupyterWidget.restart_kernel does not support extra arguments
            self.kernel_manager.restart_kernel(
                extra_arguments=self._extra_arguments())
            self._kernel_restarted_message(died=False)
        else:
            self.start_kernel()

    def getModel(self):
        return self._door_name

    def _set_door_name(self, door):
        if door:
            full_door_tg_name, door_tg_name, door_tg_alias = (
                from_name_to_tango(door))
            door_alias = door_tg_alias or door_tg_name
            self._door_name = full_door_tg_name
            self._door_alias = door_alias
        else:
            self._door_name = None
            self._door_alias = None

    def _set_macro_server_name(self, door):
        if door:
            macro_server = get_macroserver_for_door(door)
            full_ms_tg_name, ms_tg_name, ms_tg_alias = (
                from_name_to_tango(macro_server))
            ms_alias = ms_tg_alias or ms_tg_name
            self._macro_server_name = full_ms_tg_name
            self._macro_server_alias = ms_alias
        else:
            self._macro_server_name = None
            self._macro_server_alias = None

    def _set_prompts(self):
        # If traitlets >= 5.0.0 then DeferredConfigString is used for values
        # that are not listed in the configurable classes. Get its value.
        if (traitlets.version_info >= (5, 0, 0)
                and self._config_passed_as_extra_arguments):
            self.kernel_client.execute(
                "from sardana.spock.config import Spock", silent=True)
            var = "get_ipython().config.Spock.door_alias.get_value(Spock.door_alias)"  # noqa
        else:
            var = "get_ipython().config.Spock.door_alias"
        self._silent_exec_callback(
            var, self._set_prompts_callback)

    def _set_prompts_callback(self, msg):
        in_prefix = 'In'
        if msg['status'] == 'ok':
            output_bytes = msg['data']['text/plain']
            try:
                in_prefix = ast.literal_eval(output_bytes)
            except SyntaxError:
                pass

        if not self.kernel_manager.is_valid_spock_profile:
            self._print_ipython_warning()

        self.in_prompt = (
            in_prefix + ' [<span class="in-prompt-number">%i</span>]:')
        self.out_prompt = (
            'Result [<span class="out-prompt-number">%i</span>]:')

    def _print_ipython_warning(self):
        if self.use_model_from_profile or self._extra_arguments():
            self.append_stream(
                "\nSpock profile error: please run spock in the terminal"
                " and restart the kernel.\n")
        else:
            self.append_stream(
                "\nNo door selected. Please select a valid door.\n")
        self.append_stream(
            "\nThis is a normal ipython kernel. "
            "Spock functionality is not available.\n")

    def runMacro(self, macro_node):
        self.execute(macro_node.toSpockCommand())

    # Adapted from
    # https://github.com/moble/remote_exec/blob/master/remote_exec.py#L61
    def get_value(self, var, timeout=None):
        """Retrieve a value from the user namespace through a blocking call.

        The value must be able to be pickled on the kernel side and unpickled
        on the frontend side.

        The command will import the pickle module in the user namespace. This
        may overwrite a user defined variable with the same name.

        :param var:
            The name of the variable to be retrieved
        :type var:  str
        :param timeout:
            Number of seconds to wait for reply. If no reply is recieved, a
            `Queue.Empty` exception is thrown. The default is to wait
            indefinitely
        :type timeout:  int or None
        :return:
            The value of the variable from the user namespace
        """
        pickle_dumps = 'pickle.dumps({})'.format(var)
        msg_id = self.blocking_client.execute(
            "import pickle", silent=True,
            user_expressions={'output': pickle_dumps})
        reply = self.blocking_client.get_shell_msg(msg_id, timeout=timeout)
        if reply['content']['status'] != "ok":
            raise RuntimeError("{}: {}".format(
                reply['content']['ename'], reply['content']['evalue']))
        output = reply['content']['user_expressions']['output']
        if output['status'] != "ok":
            raise RuntimeError("{}: {}".format(
                output['ename'], output['evalue']))
        output_bytes = output['data']['text/plain']
        output_bytes = ast.literal_eval(output_bytes)
        return pickle.loads(output_bytes)

    def shutdown_kernel(self):
        """Cleanly shut down the kernel and client subprocesses"""
        info('Shutting down kernel...')
        if self.kernel_client:
            self.kernel_client.stop_channels()
        if self.kernel_manager and self.kernel_manager.kernel:
            self.kernel_manager.shutdown_kernel()

    def _handle_kernel_lauched(self):
        if self.kernel_client:
            self.kernel_client.kernel_info()

    def _handle_kernel_info_reply(self, rep):
        self._set_prompts()
        is_starting = self._starting
        super()._handle_kernel_info_reply(rep)
        if not is_starting:
            # The base method did not print the banner and reset the prompt.
            # As the profile might have changed, do it here.
            self._append_plain_text("\n\n")
            self._append_plain_text(self.kernel_banner)
            self.reset()


class QtSpock(TaurusMainWindow):
    """A standalone QtSpock window

    .. note::
        The `QtSpock` class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.
    """
    def __init__(self, parent=None, designMode=False):
        super().__init__(parent, designMode)
        self.spockWidget = QtSpockWidget(parent=self)
        self.registerConfigDelegate(self.spockWidget)
        self.spockWidget.setModelInConfig(True)
        self.setCentralWidget(self.spockWidget)
        self.configureAction = self.createConfigureAction()
        self.taurusMenu.addAction(self.configureAction)
        self.statusBar().showMessage("QtSpock ready")
        self.loadSettings()

    def createConfigureAction(self):
        configureAction = Qt.QAction(getThemeIcon(
            "preferences-system-session"), "Change configuration", self)
        configureAction.triggered.connect(self.changeConfiguration)
        configureAction.setToolTip("Configuring MacroServer and Door")
        configureAction.setShortcut("F10")
        return configureAction

    def changeConfiguration(self):
        """This method is used to change macroserver as a model of application.
           It shows dialog with list of all macroservers on tango host, if the
           user Cancel dialog it doesn't do anything."""
        dialog = TaurusMacroConfigurationDialog(
            self, self.spockWidget._macro_server_name,
            self.modelName)
        if dialog.exec_():
            self.spockWidget.setModel(str(dialog.doorComboBox.currentText()))
        else:
            return


def main():
    from taurus.qt.qtgui.application import TaurusApplication
    app = TaurusApplication()
    app.setOrganizationName("Taurus")
    app.setApplicationName("QtSpock")
    window = QtSpock()
    window.show()
    app.aboutToQuit.connect(window.spockWidget.shutdown_kernel)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
