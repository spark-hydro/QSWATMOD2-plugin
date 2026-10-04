"""Tests for scripts/package.py (no QGIS needed): python3 test/test_package.py"""
import hashlib
import importlib.util
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_spec = importlib.util.spec_from_file_location("package", os.path.join(_root, "scripts", "package.py"))
package = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(package)


class PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.meta = package.read_metadata()
        cls.full, _ = package.build(os.path.join(cls.tmp.name, "a"), need_linux=False)
        cls.linux, _ = package.build(os.path.join(cls.tmp.name, "b"), need_linux=False, linux_only=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_file_name_gives_the_plugin_id(self):
        # QGIS: id = file name up to the first dot
        for path in (self.full, self.linux):
            self.assertEqual(os.path.basename(path).partition(".")[0], "QSWATMOD2")
        self.assertTrue(self.linux.endswith("-linux.zip"))
        self.assertIn(self.meta["version"], os.path.basename(self.full))

    def test_layout(self):
        for path in (self.full, self.linux):
            self.assertEqual(package.check(path), [])
            names = zipfile.ZipFile(path).namelist()
            self.assertIn("QSWATMOD2/metadata.txt", names)
            self.assertFalse([n for n in names if "__pycache__" in n or n.startswith("QSWATMOD2/test/")])

    def test_linux_zip_has_no_windows_programs(self):
        full = zipfile.ZipFile(self.full).namelist()
        linux = zipfile.ZipFile(self.linux).namelist()
        self.assertTrue([n for n in full if n.endswith(".exe")])
        self.assertEqual([n for n in linux if n.endswith(".exe")], [])
        self.assertLess(len(linux), len(full))

    def test_reproducible(self):
        again, _ = package.build(os.path.join(self.tmp.name, "c"), need_linux=False)
        digest = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
        self.assertEqual(digest(self.full), digest(again))

    def test_plugins_xml(self):
        xml = package.plugins_xml(self.meta, os.path.basename(self.linux), "v9.9.9")
        node = ET.fromstring(xml).find("pyqgis_plugin")
        self.assertEqual(node.get("name"), "QSWATMOD2")
        self.assertEqual(node.get("version"), self.meta["version"])
        self.assertEqual(node.findtext("file_name"), os.path.basename(self.linux))
        self.assertEqual(
            node.findtext("download_url"),
            "https://github.com/spark-hydro/QSWATMOD2-plugin/releases/download/v9.9.9/" + os.path.basename(self.linux))
        self.assertTrue(node.findtext("icon").startswith("https://"))
        mirror = package.plugins_xml(self.meta, "x.zip", "v1", "http://localhost:8000/")
        self.assertEqual(ET.fromstring(mirror).find("pyqgis_plugin").findtext("download_url"),
                         "http://localhost:8000/x.zip")

    def test_check_finds_problems(self):
        bad = os.path.join(self.tmp.name, "bad.zip")
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("other/x.py", "1")
            z.writestr("QSWATMOD2/__pycache__/a.pyc", "1")
        self.assertTrue(package.check(bad))


if __name__ == "__main__":
    unittest.main()
