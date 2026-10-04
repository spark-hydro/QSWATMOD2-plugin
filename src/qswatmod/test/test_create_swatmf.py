"""Tests for pyfolder/create_swatmf.py (no QGIS needed): python3 test/test_create_swatmf.py

Fixtures in test/data/createswatmf/:
  *_seed*/        small random datasets; expected/ was written by the original Fortran
                  program (CreateMapFiles, compiled with gfortran) from the same input
  river_excerpt/  first 60 river cells of a real model; expected/ is the output of the
                  real CreateSWATMF.exe (byte for byte)

Set CMF_EXAMPLE=<folder> to also compare with a full example: a folder holding the four
tables (hru_dhru, dhru_grid, grid_dhru, river_grid) and the swatmf_*.txt files that
CreateSWATMF.exe wrote from them.
"""
import glob
import importlib.util
import os
import shutil
import tempfile
import unittest

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "create_swatmf", os.path.join(_here, "..", "pyfolder", "create_swatmf.py"))
cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cs)

DATA = os.path.join(_here, "data", "createswatmf")
OUT = {"dhru2hru": "swatmf_dhru2hru.txt", "dhru2grid": "swatmf_dhru2grid.txt",
       "grid2dhru": "swatmf_grid2dhru.txt", "river2grid": "swatmf_river2grid.txt"}


def _lines(path):
    with open(path, newline="") as f:
        return f.read().split("\n")


def assert_same_numbers(test, expected, got, tol=1.1e-5):
    """Same lines (blank lines in the same places) and the same numbers within `tol`.

    A fraction exactly halfway between two 5-decimal values may round either way
    (1e-5), depending on the Fortran compiler.
    """
    a, b = _lines(expected), _lines(got)
    test.assertEqual(len(a), len(b), "different number of lines in " + os.path.basename(got))
    for i, (x, y) in enumerate(zip(a, b), 1):
        tx, ty = x.split(), y.split()
        test.assertEqual(len(tx), len(ty), "line {}: {!r} vs {!r}".format(i, x, y))
        for u, v in zip(tx, ty):
            test.assertLessEqual(abs(float(u) - float(v)), tol, "line {}: {} vs {}".format(i, u, v))


class RandomDatasets(unittest.TestCase):
    def test_against_fortran(self):
        cases = sorted(glob.glob(os.path.join(DATA, "*_seed*")))
        self.assertGreaterEqual(len(cases), 3)
        for case in cases:
            with self.subTest(case=os.path.basename(case)), tempfile.TemporaryDirectory() as out:
                cs.create_map_files(case, out)
                for key in ("dhru2hru", "dhru2grid", "grid2dhru"):
                    assert_same_numbers(
                        self, os.path.join(case, "expected", OUT[key]), os.path.join(out, OUT[key]))

    def test_dhru_without_cells_gets_three_empty_lines(self):
        case = glob.glob(os.path.join(DATA, "empty_dhru_seed*"))[0]
        with tempfile.TemporaryDirectory() as out:
            cs.create_map_files(case, out)
            lines = _lines(os.path.join(out, OUT["grid2dhru"]))
            self.assertTrue(any(l.strip() == "" for l in lines[:-1]))


class RiverExcerpt(unittest.TestCase):
    def test_identical_to_the_exe(self):
        case = os.path.join(DATA, "river_excerpt")
        with tempfile.TemporaryDirectory() as out:
            shutil.copy(os.path.join(case, "river_grid"), out)
            cs.write_river2grid(out, out)
            with open(os.path.join(out, OUT["river2grid"]), "rb") as f:
                got = f.read()
        with open(os.path.join(case, "expected", OUT["river2grid"]), "rb") as f:
            self.assertEqual(got, f.read())


class Layout(unittest.TestCase):
    def test_crlf_and_columns(self):
        case = glob.glob(os.path.join(DATA, "plain_seed*"))[0]
        with tempfile.TemporaryDirectory() as out:
            paths = cs.create_map_files(case, out)
            self.assertEqual(sorted(os.path.basename(p) for p in paths), sorted(OUT.values()))
            for p in paths:
                with open(p, "rb") as f:
                    raw = f.read()
                self.assertNotIn(b"\n", raw.replace(b"\r\n", b""), p)  # every line ends in CRLF
            first = _lines(os.path.join(out, OUT["dhru2hru"]))[1]
            self.assertEqual(len(first.rstrip("\r")), 3 * 13)  # i13 columns


class Errors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        case = glob.glob(os.path.join(DATA, "plain_seed*"))[0]
        for f in ("hru_dhru", "dhru_grid", "grid_dhru", "river_grid"):
            shutil.copy(os.path.join(case, f), self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_table(self):
        os.remove(os.path.join(self.dir, "grid_dhru"))
        with self.assertRaises(FileNotFoundError):
            cs.create_map_files(self.dir)

    def test_unsorted_table(self):
        path = os.path.join(self.dir, "dhru_grid")
        with open(path) as f:
            lines = f.read().split("\n")
        head, rows = lines[:3], [l for l in lines[3:] if l]
        # put one row of the first cell after a row of another cell
        rows.insert(len(rows) - 1, rows.pop(0))
        with open(path, "w") as f:
            f.write("\n".join(head + rows) + "\n")
        with self.assertRaisesRegex(ValueError, "not sorted"):
            cs.write_dhru2grid(self.dir, self.dir)

    def test_hru_without_dhru(self):
        path = os.path.join(self.dir, "hru_dhru")
        with open(path) as f:
            lines = f.read().split("\n")
        lines[1] = str(int(lines[1]) + 1)  # one more HRU than the table has
        with open(path, "w") as f:
            f.write("\n".join(lines))
        with self.assertRaisesRegex(ValueError, "no DHRU"):
            cs.write_dhru2hru(self.dir, self.dir)


@unittest.skipUnless(os.environ.get("CMF_EXAMPLE"), "set CMF_EXAMPLE=<folder> to run")
class RealExample(unittest.TestCase):
    def test_against_the_exe(self):
        src = os.environ["CMF_EXAMPLE"]
        with tempfile.TemporaryDirectory() as out:
            cs.create_map_files(src, out)
            for name in OUT.values():
                if os.path.exists(os.path.join(src, name)):
                    with self.subTest(file=name):
                        assert_same_numbers(self, os.path.join(src, name), os.path.join(out, name))


if __name__ == "__main__":
    unittest.main()
