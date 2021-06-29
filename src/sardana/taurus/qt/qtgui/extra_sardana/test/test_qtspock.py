import re
import os
import tempfile
import qtconsole
import numpy as np
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from taurus.external.unittest import TestCase, main, skipIf
from taurus.external import qt
from taurus.external.qt import Qt
from sardana.spock.ipython_01_00.genutils import _create_config_file, \
    from_name_to_tango
from sardana.sardanacustomsettings import UNITTEST_DOOR_NAME
from sardana.taurus.qt.qtgui.extra_sardana.qtspock import QtSpockWidget, \
    get_spock_profile_dir

if qt.PYQT4:
    from PyQt4.QtTest import QTest
elif qt.PYQT5:
    from PyQt5.QtTest import QTest
elif qt.PYSIDE:
    from PySide.QtTest import QTest


app = Qt.QApplication.instance()
if not app:
    app = Qt.QApplication([])


def waitFor(predicate, timeout):
    """Process events until predicate is true or timeout seconds passed

    This seems to not handle the destruction of widget correctly, use
    waitForLoop in such cases.
    """
    if predicate():
        return True

    timer = Qt.QElapsedTimer()
    timer.start()

    while not timer.hasExpired(timeout):
        QTest.qWait(min(100, timeout - timer.elapsed()))
        if predicate():
            return True

    return predicate()


def waitForLoop(predicate, timeout):
    """Run event loop and periodically check for predicate"""
    if predicate():
        return True

    timer = Qt.QElapsedTimer()
    timer.start()

    loop = Qt.QEventLoop()

    while not timer.hasExpired(timeout):
        Qt.QTimer.singleShot(min(100, timeout - timer.elapsed()), loop.quit)
        loop.exec_()
        if predicate():
            return True

    return predicate()


class QtSpockBaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Use setUpClass instead of setUp because starting QtSpock
        # takes a relatively long time.
        cls.test_ipython_dir = tempfile.mkdtemp()
        cls._create_profile()
        os.environ["IPYTHONDIR"] = cls.test_ipython_dir
        cls._isDestroyed = False

    @classmethod
    def _create_profile(cls):
        cls.test_spockdoor_dir = os.path.join(
            cls.test_ipython_dir, "profile_spockdoor")
        os.mkdir(cls.test_spockdoor_dir)
        _create_config_file(cls.test_spockdoor_dir, UNITTEST_DOOR_NAME)

    @classmethod
    def _handle_destroyed(cls):
        cls._isDestroyed = True

    @classmethod
    def tearDownClass(cls):
        cls.widget.shutdown_kernel()
        cls.widget.setAttribute(Qt.Qt.WA_DeleteOnClose)
        cls.widget.destroyed.connect(cls._handle_destroyed)
        cls.widget.close()
        cls.widget = None
        waitForLoop(lambda: cls._isDestroyed, 5000)


class QtSpockTestCase(QtSpockBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(QtSpockTestCase, cls).setUpClass()
        cls.widget = QtSpockWidget(use_model_from_profile=True)
        cls.widget.start_kernel()
        cls.widget.show()


class CorrectProfileOutputMixin(object):
    def test_spock_banner(self):
        def predicate():
            text = self.widget._control.toPlainText()
            matches = re.findall(r"^Spock \d\.\d", text, re.MULTILINE)
            return len(matches) == 1
        self.assertTrue(waitFor(predicate, 10000))

    def test_spock_prompt(self):
        full_name, name, alias = from_name_to_tango(UNITTEST_DOOR_NAME)
        alias = alias or name

        def predicate():
            text = self.widget._control.toPlainText()
            matches = re.findall(
                r"^{}.*\[(\d)\]".format(alias),
                text, re.MULTILINE)
            return len(matches) == 1 and matches[0] == "1"
        self.assertTrue(waitFor(predicate, 10000))


class CorrectProfileTestCase(QtSpockTestCase, CorrectProfileOutputMixin):

    @skipIf(qtconsole.version_info >= (4, 4, 0),
            "blocking_client was removed in qtconsole#174")
    def test_get_value(self):
        msg_id = self.widget.blocking_client.execute(
            "a = arange(3)", silent=True)
        self.widget.blocking_client.get_shell_msg(msg_id)
        self.assertTrue(
            np.array_equal(self.widget.get_value("a"), np.arange(3)))

    def test_find_spock_profile(self):
        self.assertEqual(
            get_spock_profile_dir("spockdoor"), self.test_spockdoor_dir)

    def test_is_valid_spock_profile(self):
        self.assertTrue(self.widget.kernel_manager.is_valid_spock_profile)


class ProfileErrorOutputMixin(object):
    def test_ipython_banner(self):
        def predicate():
            text = self.widget._control.toPlainText()
            matches = re.findall(r"^IPython \d\.\d", text, re.MULTILINE)
            return len(matches) == 1
        self.assertTrue(waitFor(predicate, 10000))

    def test_ipython_prompt(self):
        def predicate():
            text = self.widget._control.toPlainText()
            matches = re.findall(r"^In.*\[(\d)\]", text, re.MULTILINE)
            return len(matches) == 1 and matches[0] == "1"
        self.assertTrue(waitFor(predicate, 10000))

    def test_profile_error_info(self):
        def predicate():
            text = self.widget._control.toPlainText()
            matches = re.findall(r"^Spock profile error", text, re.MULTILINE)
            return len(matches) == 1
        self.assertTrue(waitFor(predicate, 10000))


class MissingProfileTestCase(QtSpockTestCase, ProfileErrorOutputMixin):
    @classmethod
    def setUpClass(cls):
        cls.test_ipython_dir = tempfile.mkdtemp()
        os.environ["IPYTHONDIR"] = cls.test_ipython_dir
        cls.widget = QtSpockWidget(use_model_from_profile=True)
        cls.widget.start_kernel()
        cls.widget.show()
        cls._isDestroyed = False

    def test_is_valid_spock_profile(self):
        self.assertTrue(not self.widget.kernel_manager.is_valid_spock_profile)


class CorrectProfileAfterRestartTestCase(
        MissingProfileTestCase, CorrectProfileOutputMixin):
    @classmethod
    def setUpClass(cls):
        super(CorrectProfileAfterRestartTestCase, cls).setUpClass()

        # Wait until startup finished
        def predicate():
            text = cls.widget._control.toPlainText()
            matches = re.findall(r"\[1\]: $", text, re.MULTILINE)
            return len(matches) == 1
        assert waitFor(predicate, 10000)

        cls._create_profile()

        # Restart kernel
        def acceptDialog():
            topLevelWidgets = Qt.QApplication.topLevelWidgets()
            dialog = None
            for widget in topLevelWidgets:
                if isinstance(widget, Qt.QMessageBox):
                    dialog = widget
            dialog.button(Qt.QMessageBox.Yes).click()

        Qt.QTimer.singleShot(10, acceptDialog)
        cls.widget.restart_kernel("Restart?")

    def test_is_valid_spock_profile(self):
        self.assertTrue(self.widget.kernel_manager.is_valid_spock_profile)


class ProfileErrorAfterRestartTestCase(
        QtSpockTestCase, ProfileErrorOutputMixin):
    @classmethod
    def setUpClass(cls):
        super(ProfileErrorAfterRestartTestCase, cls).setUpClass()

        # Wait until startup finished
        def predicate():
            text = cls.widget._control.toPlainText()
            matches = re.findall(r"\[1\]: $", text, re.MULTILINE)
            return len(matches) == 1
        assert waitFor(predicate, 10000)

        # "Update" profile
        config_file = os.path.join(
            cls.test_spockdoor_dir, "ipython_config.py")
        with open(config_file) as f:
            config = f.read()
        config = re.sub(
            r"^# spock_creation_version = \d\.\d.*",
            "# spock_creation_version = 9.9.9-gamma",
            config, flags=re.MULTILINE)
        with open(config_file, 'w') as f:
            f.write(config)

        # Restart kernel
        cls.widget.kernel_manager.restart_kernel()

    def test_is_valid_spock_profile(self):
        self.assertTrue(not self.widget.kernel_manager.is_valid_spock_profile)


class QtSpockNoModelTestCase(QtSpockBaseTestCase, ProfileErrorOutputMixin):
    @classmethod
    def setUpClass(cls):
        super(QtSpockNoModelTestCase, cls).setUpClass()
        cls.widget = QtSpockWidget()
        cls.widget.start_kernel()
        cls.widget.show()

    def test_is_valid_spock_profile(self):
        self.assertTrue(not self.widget.kernel_manager.is_valid_spock_profile)

    def test_profile_error_info(self):
        def predicate():
            text = self.widget._control.toPlainText()
            matches = re.findall(r"^No door selected", text, re.MULTILINE)
            return len(matches) == 1
        self.assertTrue(waitFor(predicate, 10000))


class QtSpockModelTestCase(QtSpockBaseTestCase, CorrectProfileOutputMixin):
    @classmethod
    def setUpClass(cls):
        super(QtSpockModelTestCase, cls).setUpClass()
        cls.widget = QtSpockWidget()
        cls.widget.setModel(UNITTEST_DOOR_NAME)
        cls.widget.show()

    def test_is_valid_spock_profile(self):
        self.assertTrue(self.widget.kernel_manager.is_valid_spock_profile)

    def test_setModel_twice_no_restart(self):
        with patch.object(
                self.widget.kernel_manager, "restart_kernel", spec=True) as m:
            self.widget.setModel(UNITTEST_DOOR_NAME)
            self.assertTrue(not m.called)


class QtSpockModelAfterRestartTestCase(
        QtSpockBaseTestCase, CorrectProfileOutputMixin):
    @classmethod
    def setUpClass(cls):
        super(QtSpockModelAfterRestartTestCase, cls).setUpClass()
        cls.widget = QtSpockWidget()
        cls.widget.start_kernel()
        cls.widget.show()

        # Wait until startup finished
        def predicate():
            text = cls.widget._control.toPlainText()
            matches = re.findall(r"\[1\]: $", text, re.MULTILINE)
            return len(matches) == 1
        assert waitFor(predicate, 10000)

        cls.widget.setModel(UNITTEST_DOOR_NAME)

    def test_is_valid_spock_profile(self):
        self.assertTrue(self.widget.kernel_manager.is_valid_spock_profile)


class QtSpockNoModelAfterRestartTestCase(QtSpockNoModelTestCase):
    @classmethod
    def setUpClass(cls):
        # Do only call the original base class constructor
        super(QtSpockNoModelTestCase, cls).setUpClass()
        cls.widget = QtSpockWidget()
        cls.widget.setModel(UNITTEST_DOOR_NAME)
        cls.widget.show()

        # Wait until startup finished
        def predicate():
            text = cls.widget._control.toPlainText()
            matches = re.findall(r"\[1\]: $", text, re.MULTILINE)
            return len(matches) == 1
        assert waitFor(predicate, 10000)

        cls.widget.setModel("")


class QtSpockModelMissingProfileTestCase(
        QtSpockTestCase, ProfileErrorOutputMixin):
    @classmethod
    def setUpClass(cls):
        cls.test_ipython_dir = tempfile.mkdtemp()
        os.environ["IPYTHONDIR"] = cls.test_ipython_dir
        cls.widget = QtSpockWidget()
        cls.widget.setModel(UNITTEST_DOOR_NAME)
        cls.widget.show()
        cls._isDestroyed = False

    def test_is_valid_spock_profile(self):
        self.assertTrue(not self.widget.kernel_manager.is_valid_spock_profile)


if __name__ == '__main__':
    main()
