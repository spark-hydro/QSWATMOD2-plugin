"""Tests for pyfolder/sysutil.py (no QGIS needed): run with `python3 test/test_sysutil.py`."""
import importlib.util
import os
import stat
import tempfile
import unittest
from unittest import mock

_path = os.path.join(os.path.dirname(__file__), "..", "pyfolder", "sysutil.py")
_spec = importlib.util.spec_from_file_location("sysutil", _path)
sysutil = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sysutil)


class OpenFileTest(unittest.TestCase):
    def test_linux_uses_xdg_open(self):
        with mock.patch.object(sysutil.sys, "platform", "linux"), \
                mock.patch.object(sysutil.subprocess, "Popen") as popen:
            sysutil.open_file("/tmp/a/../out.gif")
        popen.assert_called_once_with(["xdg-open", os.path.normpath("/tmp/out.gif")])

    def test_macos_uses_open(self):
        with mock.patch.object(sysutil.sys, "platform", "darwin"), \
                mock.patch.object(sysutil.subprocess, "Popen") as popen:
            sysutil.open_file("/tmp/out.mp4")
        popen.assert_called_once_with(["open", os.path.normpath("/tmp/out.mp4")])

    def test_windows_uses_startfile(self):
        with mock.patch.object(sysutil.sys, "platform", "win32"), \
                mock.patch.object(sysutil.os, "startfile", create=True) as sf:
            sysutil.open_file("C:/x/out.gif")
        sf.assert_called_once_with(os.path.normpath("C:/x/out.gif"))


def _touch(folder, *names):
    for n in names:
        open(os.path.join(folder, n), "w").close()


class FindExeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_nothing_found(self):
        self.assertIsNone(sysutil.find_swatmf_exe(self.dir, "linux"))
        self.assertIsNone(sysutil.find_swatmf_exe(self.dir, "win32"))

    def test_windows_old_programs_keep_their_priority(self):
        _touch(self.dir, "SWAT-MODFLOW3.exe")
        self.assertEqual(os.path.basename(sysutil.find_swatmf_exe(self.dir, "win32")),
                         "SWAT-MODFLOW3.exe")
        _touch(self.dir, "swatmf_rel230818.exe")
        self.assertEqual(os.path.basename(sysutil.find_swatmf_exe(self.dir, "win32")),
                         "swatmf_rel230818.exe")

    def test_windows_prefers_the_release_program(self):
        _touch(self.dir, "swatmf_rel230818.exe", "SWAT-MODFLOW3.exe",
               "swatmf3-v1.2.9-gnu-win_amd64-Rel.exe", "swatmf3-v1.2.10-gnu-win_amd64-Rel.exe",
               "swatmf3-v1.2.10-gnu-win_amd64-Rel.zip")
        self.assertEqual(os.path.basename(sysutil.find_swatmf_exe(self.dir, "win32")),
                         "swatmf3-v1.2.10-gnu-win_amd64-Rel.exe")
        _touch(self.dir, "swatmf3.exe")
        self.assertEqual(os.path.basename(sysutil.find_swatmf_exe(self.dir, "win32")),
                         "swatmf3.exe")

    def test_windows_ignores_the_linux_program(self):
        _touch(self.dir, "swatmf3", "swatmf3-v1.2.5-gnu-lin_x86_64-Rel")
        self.assertIsNone(sysutil.find_swatmf_exe(self.dir, "win32"))

    def test_linux_ignores_exe_files(self):
        _touch(self.dir, "SWAT-MODFLOW3.exe", "swatmf_rel230818.exe", "swatmf3.exe")
        self.assertIsNone(sysutil.find_swatmf_exe(self.dir, "linux"))

    def test_linux_prefers_plain_name_then_newest_release(self):
        _touch(self.dir, "swatmf3-v1.2.9-gnu-lin_x86_64-Rel",
               "swatmf3-v1.2.10-gnu-lin_x86_64-Rel",
               "swatmf3-v1.2.10-gnu-lin_x86_64-Rel.zip")
        self.assertEqual(os.path.basename(sysutil.find_swatmf_exe(self.dir, "linux")),
                         "swatmf3-v1.2.10-gnu-lin_x86_64-Rel")
        _touch(self.dir, "swatmf3")
        self.assertEqual(os.path.basename(sysutil.find_swatmf_exe(self.dir, "linux")),
                         "swatmf3")

    @unittest.skipIf(os.name == "nt", "no execute bit on Windows")
    def test_ensure_executable(self):
        _touch(self.dir, "swatmf3")
        path = os.path.join(self.dir, "swatmf3")
        os.chmod(path, 0o644)
        sysutil.ensure_executable(path)
        self.assertTrue(os.stat(path).st_mode & stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
