"""Create the SWAT-MODFLOW linkage files (replaces CreateSWATMF.exe).

CreateSWATMF.exe was a small Fortran program (CreateMapFiles). It reads four tables
written by the plugin into GIS/Table and writes four mapping files that SWAT-MODFLOW3
reads. This module does the same with numpy, so it runs on Windows, Linux and macOS.

    hru_dhru   -> swatmf_dhru2hru.txt    DHRUs of each HRU, with area fractions
    dhru_grid  -> swatmf_dhru2grid.txt   DHRUs of each MODFLOW cell, with area fractions
    grid_dhru  -> swatmf_grid2dhru.txt   row, column and area fractions of each DHRU's cells
    river_grid -> swatmf_river2grid.txt  subbasins and river lengths of each river cell

Same layout as the program wrote: integers in 13 columns, fractions as f13.5 computed in
single precision, CRLF line ends. The only difference is rounding of a fraction that is
exactly halfway between two 5-decimal values (<= 1e-5, the Fortran runtime decided it
differently from one compiler to the next).
"""
import os

import numpy as np

NL = "\r\n"


def _read(path, nhead):
    """First token of each of the `nhead` header lines (as text) and the data table."""
    with open(path) as f:
        heads = []
        for _ in range(nhead):
            tokens = f.readline().split()
            heads.append(tokens[0] if tokens else "")
    return heads, np.loadtxt(path, skiprows=nhead, ndmin=2)


def _ints(a):
    return "".join("%13d" % v for v in a) + NL


def _fracs(a):
    return "".join("%13.5f" % v for v in a) + NL


def _group(key, what):
    """Start/end index of each run of equal `key` values. The table must be grouped."""
    starts = np.flatnonzero(np.diff(key, prepend=key[0] - 1))
    seen = key[starts]
    if len(np.unique(seen)) != len(seen):
        raise ValueError("{} is not sorted: the same id appears in separate places".format(what))
    return starts, np.append(starts[1:], len(key))


def _table(path, nhead, nvalues, nlines_head):
    heads, a = _read(path, nhead)
    n = int(float(heads[nlines_head]))
    if a.shape[0] < n or a.shape[1] < nvalues:
        raise ValueError("{}: expected {} lines of {} values, found {}".format(
            os.path.basename(path), n, nvalues, a.shape))
    return [int(float(h)) for h in heads[:nhead - 1]], a[:n]


def write_dhru2hru(table_dir, out_dir):
    heads, a = _table(os.path.join(table_dir, "hru_dhru"), 3, 5, 0)
    nhru = heads[1]
    dhru, hru, sub = a[:, 0].astype(int), a[:, 2].astype(int), a[:, 3].astype(int)
    frac = a[:, 1].astype(np.float32) / a[:, 4].astype(np.float32)
    starts, ends = _group(hru, "hru_dhru (HRU_ID)")
    present = set(hru[starts].tolist())
    missing = [h for h in range(1, nhru + 1) if h not in present]
    if missing:
        raise ValueError("hru_dhru: HRU {} has no DHRU".format(missing[0]))
    with open(os.path.join(out_dir, "swatmf_dhru2hru.txt"), "w", newline="") as o:
        o.write(_ints([nhru, (ends - starts).max()]))
        for s, e in zip(starts, ends):
            o.write(_ints([hru[s], e - s, sub[e - 1]]))
            o.write(_ints(dhru[s:e]))
            o.write(_fracs(frac[s:e]))


def write_dhru2grid(table_dir, out_dir):
    heads, a = _table(os.path.join(table_dir, "dhru_grid"), 3, 5, 0)
    ncells = heads[1]
    cell, dhru = a[:, 0].astype(int), a[:, 2].astype(int)
    frac = a[:, 3].astype(np.float32) / a[:, 1].astype(np.float32)
    starts, ends = _group(cell, "dhru_grid (grid_id)")
    where = {int(cell[s]): (s, e) for s, e in zip(starts, ends)}
    with open(os.path.join(out_dir, "swatmf_dhru2grid.txt"), "w", newline="") as o:
        o.write(_ints([ncells, (ends - starts).max()]))
        for n in range(1, ncells + 1):
            se = where.get(n)
            o.write(_ints([n, 0 if se is None else se[1] - se[0]]))
            if se:  # a cell without DHRUs gets only the count line
                o.write(_ints(dhru[se[0]:se[1]]))
                o.write(_fracs(frac[se[0]:se[1]]))


def write_grid2dhru(table_dir, out_dir):
    heads, a = _table(os.path.join(table_dir, "grid_dhru"), 5, 5, 0)
    ndhru, ncol = heads[1], heads[3]
    cell, dhru = a[:, 0].astype(int), a[:, 2].astype(int)
    frac = a[:, 3].astype(np.float32) / a[:, 4].astype(np.float32)
    # row and column as CreateMapFiles computed them (kept as is)
    row = cell // ncol + 1
    col = cell - ncol * (row - 1)
    starts, ends = _group(dhru, "grid_dhru (dhru_id)")
    where = {int(dhru[s]): (s, e) for s, e in zip(starts, ends)}
    with open(os.path.join(out_dir, "swatmf_grid2dhru.txt"), "w", newline="") as o:
        o.write(_ints([ndhru, (ends - starts).max()]))
        for n in range(1, ndhru + 1):
            se = where.get(n)
            o.write(_ints([n, 0 if se is None else se[1] - se[0]]))
            if se is None:  # a DHRU without cells gets three empty lines
                o.write((" " + NL) * 3)
                continue
            s, e = se
            o.write(_ints(row[s:e]))
            o.write(_ints(col[s:e]))
            o.write(_fracs(frac[s:e]))


def write_river2grid(table_dir, out_dir):
    _, a = _read(os.path.join(table_dir, "river_grid"), 2)
    grid, sub, length = a[:, 0].astype(int), a[:, 1].astype(int), a[:, 2].astype(np.float32)
    # river cells in the order they first appear; a cell can cross several subbasins
    uniq, first, inverse = np.unique(grid, return_index=True, return_inverse=True)
    with open(os.path.join(out_dir, "swatmf_river2grid.txt"), "w", newline="") as o:
        o.write("%12d" % len(uniq) + NL)
        for i, u in enumerate(np.argsort(first), 1):
            rows = np.flatnonzero(inverse == u)
            o.write(_ints([i, uniq[u], len(rows)]))
            o.write(_ints(sub[rows]))
            o.write(_fracs(length[rows]))


WRITERS = [
    ("river_grid", write_river2grid),
    ("hru_dhru", write_dhru2hru),
    ("dhru_grid", write_dhru2grid),
    ("grid_dhru", write_grid2dhru),
]


def create_map_files(table_dir, out_dir=None, progress=None):
    """Write the four swatmf_*.txt mapping files from the tables in `table_dir`.

    `out_dir` defaults to `table_dir`. `progress(message)` is called before each file.
    Returns the paths written.
    """
    out_dir = out_dir or table_dir
    for name, _ in WRITERS:
        if not os.path.isfile(os.path.join(table_dir, name)):
            raise FileNotFoundError(
                "{} is missing in {} (export the linkage tables first)".format(name, table_dir))
    written = []
    for name, writer in WRITERS:
        if progress:
            progress("Writing the mapping from {} ...".format(name))
        writer(table_dir, out_dir)
    for out in ("swatmf_river2grid.txt", "swatmf_dhru2hru.txt",
                "swatmf_dhru2grid.txt", "swatmf_grid2dhru.txt"):
        written.append(os.path.join(out_dir, out))
    return written
