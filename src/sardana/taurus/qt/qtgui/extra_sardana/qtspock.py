"""A RichJupyterWidget that loads a spock profile.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import (bytes, str, open, super, range,  # noqa
                      zip, round, input, int, pow, object)

import sys

from taurus.external.qt import Qt

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager


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

        self.kernel_manager = QtKernelManager(kernel_name=kernel)
        self.kernel_manager.start_kernel(
            extra_arguments=["--profile", profile])

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

    def shutdown_kernel(self):
        """Cleanly shut down the kernel and client subprocesses"""
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()


def main():
    app = Qt.QApplication(sys.argv)
    widget = QtSpockWidget()
    widget.show()
    app.aboutToQuit.connect(widget.shutdown_kernel)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
