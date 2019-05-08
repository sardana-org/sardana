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
try:
    # IPython 4.x
    from IPython.paths import get_ipython_dir
except:
    # IPython <4.x
    from IPython.utils.path import get_ipython_dir

from taurus.external.qt import Qt
from taurus import info

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager

from sardana import release
from sardana.spock.ipython_01_00.genutils import get_profile_metadata


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
    def __init__(self, profile='spockdoor', kernel='python2', **kw):
        super().__init__(**kw)

        if self.check_spock_profile(profile):
            self.kernel_manager = QtKernelManager(kernel_name=kernel)
            info('Starting kernel...')
            self.kernel_manager.start_kernel(
                extra_arguments=["--profile", profile])

            self.kernel_client = self.kernel_manager.client()
            self.kernel_client.start_channels()
            self.in_prompt = self.get_value(
                "get_ipython().config.Spock.door_alias")
            self.in_prompt += ' [<span class="in-prompt-number">%i</span>]:'
            self.out_prompt = ('Result '
                               '[<span class="out-prompt-number">%i</span>]:')
        else:
            self.append_stream(
                "Spock profile error: please close the application"
                " and run spock in the terminal.")

    def get_spock_profile_dir(self, profile):
        """Return the path to the profile with the given name."""
        try:
            profile_dir = ProfileDir.find_profile_dir_by_name(
                get_ipython_dir(), profile, self.config)
        except ProfileDirError:
            return None
        return profile_dir.location

    def check_spock_profile(self, profile):
        """Check if the profile exists and has the correct value"""
        profile_dir = self.get_spock_profile_dir(profile)
        if profile_dir:
            profile_version_str, door_name = get_profile_metadata(profile_dir)
            if profile_version_str == release.version:
                return True
        return False

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


def main():
    app = Qt.QApplication(sys.argv)
    widget = QtSpockWidget()
    widget.show()
    app.aboutToQuit.connect(widget.shutdown_kernel)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
