"""A RichJupyterWidget that loads a spock profile.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import (bytes, str, open, super, range,  # noqa
                      zip, round, input, int, pow, object)

import sys
import pickle
import ast

from IPython.core.profiledir import ProfileDirError, ProfileDir

from taurus.external.qt import Qt
from taurus import info, error

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager

from sardana import release
from sardana.spock.ipython_01_00.genutils import get_profile_metadata


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

    If the check fails, i.e., the profile does not exist or has a different
    version, an ipython kernel without spock functionality is started instead
    and the attribute `valid_spock_profile` is set to `False`.
    """
    kernel_about_to_launch = Qt.pyqtSignal()

    def _launch_kernel(self, kernel_cmd, **kw):
        try:
            profile = kernel_cmd[kernel_cmd.index("--profile") + 1]
        except ValueError:
            profile = "spockdoor"
            kernel_cmd.append(["--profile", profile])
        if check_spock_profile(profile):
            self.is_valid_spock_profile = True
        else:
            index = kernel_cmd.index("--profile")
            del kernel_cmd[index]
            del kernel_cmd[index]
            self.is_valid_spock_profile = False
            error("Checking spock profile failed.")
        info('Starting kernel...')
        self.kernel_about_to_launch.emit()
        return super()._launch_kernel(kernel_cmd, **kw)


class QtSpockWidget(RichJupyterWidget):
    """A RichJupyterWidget that starts a kernel with a spock profile.

    It is important to call `shutdown_kernel` to gracefully clean up the
    started subprocesses.

    Useful methods of the base class include execute, interrupt_kernel,
    restart_kernel, and clear.

    Parameters
    ----------
    profile : string
        The name of the spock profile to use. The default is 'spockdoor'.
    kernel : string
        The name of the kernel to use. The default is 'python2'.
    **kwargs
        All remaining keywords are passed to the RichJupyterWidget base class

    Examples
    --------
    >>> from taurus.external.qt import Qt
    >>> from sardana.taurus.qt.qtgui.extra_sardana.qtspock import QtSpockWidget
    >>> app = Qt.QApplication([])
    ... widget = QtSpockWidget()
    ... widget.show()
    ... app.aboutToQuit.connect(widget.shutdown_kernel)
    ... app.exec_()
    """
    def __init__(
            self,
            profile='spockdoor',
            extensions=None,
            kernel='python2',
            **kw):
        super().__init__(**kw)

        if extensions is None:
            extensions = []
        extensions.insert(
            0, "sardana.taurus.qt.qtgui.extra_sardana.qtspock_ext")

        extra_arguments = ["--profile", profile]
        for ext in extensions:
            extra_arguments.extend(["--ext", ext])

        self.kernel_manager = SpockKernelManager(kernel_name=kernel)
        self.kernel_manager.kernel_about_to_launch.connect(
            self._handle_kernel_lauched)
        self.kernel_manager.start_kernel(extra_arguments=extra_arguments)

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

    def _set_prompts(self):
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
            self.append_stream(
                "\nSpock profile error: please run spock in the terminal and "
                "restart the kernel.\n"
                "\nThis is a normal ipython kernel. "
                "Spock functionality is not available.\n")

        self.in_prompt = (
            in_prefix + ' [<span class="in-prompt-number">%i</span>]:')
        self.out_prompt = (
            'Result [<span class="out-prompt-number">%i</span>]:')

    # Adapted from
    # https://github.com/moble/remote_exec/blob/master/remote_exec.py#L61
    def get_value(self, var, timeout=None):
        """Retrieve a value from the user namespace through a blocking call.

        The value must be able to be pickled on the kernel side and unpickled
        on the frontend side.

        The command will import the pickle module in the user namespace. This
        may overwrite a user defined variable with the same name.

        Parameters
        ----------
        var : str
            The name of the variable to be retrieved
        timeout : int or None
            Number of seconds to wait for reply. If no reply is recieved, a
            `Queue.Empty` exception is thrown. The default is to wait
            indefinitely

        Returns
        -------
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


def main():
    app = Qt.QApplication(sys.argv)
    widget = QtSpockWidget()
    widget.show()
    app.aboutToQuit.connect(widget.shutdown_kernel)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
