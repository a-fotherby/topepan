import pathlib
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

_directory = None
# Which code wrote the directory `data_cats` was last pointed at, and -- for MIN3P, which names its
# output after the run rather than after the quantity -- what that run was called. Set by
# `data_cats` and read by `read_tecplot`, which is the only other function that opens a file.
_simulator = 'crunchtope'
_run_name = None
# The snapshot indices each category actually has, and the file each one came from. Built by
# `data_cats`, because neither code guarantees a category is written at every output time, or that
# the numbering starts where the other's does.
_snapshots = {}
_files = {}

# MIN3P records the output time on the TecPlot zone line, e.g.
#   zone t = "C_j, X_i, T =   3.000000E+000 days", i =   81, j =   81, k =    1,  f=point
# It is the only place a spatial snapshot's time appears -- the filename carries an index only.
_ZONE_TIME = re.compile(r'\bT\s*=\s*([-+0-9.eEdD]+)')


def _output_path(file_cat, file_num):
    """Where this run keeps one snapshot of one output category.

    CrunchTope names a file after the quantity and the snapshot, `conc1.tec`; MIN3P names it after
    the run and the snapshot, with the quantity as the extension, `dissol_1.gsc`.
    """
    known = _files.get((file_cat, file_num))

    if known is not None:
        return known

    # Not catalogued -- either data_cats has not run or the caller has asked for a snapshot this
    # category does not have. Construct the conventional name so the error names a real path.
    directory = pathlib.Path(_directory) if _directory is not None else pathlib.Path()

    if _simulator == 'min3p':
        return directory / f'{_run_name}_{file_num}.{file_cat}'

    return directory / f'{file_cat}{file_num}.tec'


def read_tecplot(file_cat, file_num):
    file_name = str(_output_path(file_cat, file_num))
    with open(file_name) as f:
        f.readline()
        header_line = f.readline()
        headers = header_line.split('"')
        column_headers = []
        for string in headers:
            # What sits between two quoted names is a separator, not a name. CrunchTope separates
            # its with spaces alone, so testing for whitespace was enough; MIN3P separates its with
            # commas, and those survived the test and came through as duplicate empty columns.
            if string.strip().strip(',').strip():
                column_headers.append(string)
        column_headers = column_headers[1:]
        df = pd.read_csv(file_name, sep=' ', skipinitialspace=True, skiprows=[0, 1, 2], names=column_headers)
        # CrunchTope drops the 'E' from an exponent that needs three digits, writing
        # '1.2345-100'. Repaired by requiring a digit on *both* sides: a lookahead for the digits
        # alone would also match the leading minus of an ordinary negative value, turning a cell
        # holding '-100.0' into 'e-100.0' and failing to_numeric on it.
        df = df.replace(r'(\d)-(\d)', r'\1e-\2', regex=True)
        df = df.replace(r'Ee', 'e', regex=True)
        for i in column_headers:
            try:
                df[i] = pd.to_numeric(df[i], downcast="float")
            except:
                print(f'Error with {i}')

        # MIN3P spells its axes in lower case. Renamed on the way in rather than handled at every
        # use, so everything downstream -- the variable list, which starts after the three axes,
        # and the profile itself -- sees the one spelling.
        df = df.rename(columns={'x': 'X', 'y': 'Y', 'z': 'Z'})
        column_headers = ['X' if name == 'x' else 'Y' if name == 'y' else 'Z' if name == 'z'
                          else name for name in column_headers]

        return df, column_headers


def map_axes(data_frame):
    """The two spatial axes a map should be drawn over, as (across, up).

    Whichever two actually vary, so a slice in X-Z is mapped over X and Z rather than over an X-Y
    that has only one row in it.

    Raises:
        ValueError: if fewer than two axes vary, which means this is a column or a single cell
            rather than anything mappable.
    """
    present = [name for name in ('X', 'Y', 'Z') if name in data_frame]
    varying = [name for name in present if data_frame[name].nunique() > 1]

    if len(varying) < 2:
        raise ValueError(f'need two spatial axes to map, but only {varying or "none"} varies; '
                         f'this output is 1-D, so draw a profile instead')

    return varying[0], varying[1]


def tecplot_2d(data_frame, scalar_name, vmin=None, vmax=None, axis=None, colorbar=True):
    """Filled contour map of one scalar over the two axes that vary.

    Args:
        vmin, vmax: Limits for the colour scale. Left to matplotlib if either is None, which is
            what a single snapshot wants; pass `plot_var_range` output to hold the scale still
            across a series.
        axis: Axes to draw on. A new figure is made if omitted.

    Returns:
        The axes drawn on.
    """
    across, up = map_axes(data_frame)
    # Keyword arguments: pandas 2.0 removed the positional form of pivot, so the original call
    # raised TypeError on any current pandas.
    grid = data_frame.pivot(index=up, columns=across, values=scalar_name)
    axis = axis or plt.subplots()[1]

    x, y = np.meshgrid(grid.columns.values, grid.index.values)
    # Autoscale unless both limits are given, rather than handing linspace a None.
    levels = np.linspace(vmin, vmax, 16) if None not in (vmin, vmax) else 16
    contours = axis.contourf(x, y, grid.values, levels=levels, cmap=cm.viridis, extend='both')

    # The columns of the pivot are the horizontal axis and its index the vertical one. The labels
    # used to say the opposite of that, naming each axis after the other.
    axis.set_xlabel(f'{across} (m)')
    axis.set_ylabel(f'{up} (m)')

    if colorbar:
        axis.figure.colorbar(contours, ax=axis, label=scalar_name)

    return axis


def first_snapshot(file_cat):
    """The first snapshot number of a category: 1 under CrunchTope, 0 under MIN3P."""
    return next(iter(snapshot_indices(file_cat)), 1)


def initialise1D(file_cat, vertical=True):
    """Set up an empty 1-D profile.

    Args:
        vertical: Depth convention -- distance down the y axis, value across the top. This is how
            the column browser has always drawn, and stays the default. False puts distance on the
            x axis instead, which reads better for a flow path than for a depth.
    """
    df, column_headers = read_tecplot(file_cat, first_snapshot(file_cat))
    fig, ax = plt.subplots(figsize=(9, 6))
    space = profile_axis(df)
    zeros = np.zeros_like(df[space])
    line, = ax.plot(*((zeros, df[space]) if vertical else (df[space], zeros)))

    if vertical:
        ax.invert_yaxis()
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')

    ax.set_ylabel(space if vertical else '')
    ax.set_xlabel('' if vertical else space)

    return fig, ax, line


def draw_profile(ax, distance, values, vertical=True, lower=None, upper=None, value_label='',
                 log10=False, space_label='X'):
    """Draw a 1-D profile, in whichever orientation, replacing whatever the axes held.

    The axes are cleared and redrawn rather than the existing line being repointed, because
    switching orientation means changing the inversion and which side the value axis is ticked on,
    not just the data. At a hundred cells the redraw is not noticeable, and it keeps the two
    orientations from disagreeing about the state of the axes.

    Args:
        distance: The spatial coordinate, i.e. the column.
        values: What to plot along it.
        vertical: Depth convention -- distance down the y axis, value across the top.
        lower, upper: Limits for the value axis, whichever axis that turns out to be.
        value_label: Labels the value axis.
        space_label: Labels the spatial axis. Defaults to X, but a column may run down any axis --
            see `profile_axis`.
        log10: Plot log10 of the magnitude, for a quantity spanning orders of magnitude. The
            absolute value is taken because rates are signed, so the sign is lost -- the label says
            so rather than leaving it to be inferred.
    """
    if log10:
        values = np.log10(np.abs(np.asarray(values, dtype=float)))
        value_label = f'log10 |{value_label}|' if value_label else 'log10 |value|'

        if lower is not None:
            # A limit at or through zero has no logarithm; fall back to autoscaling rather than
            # handing matplotlib a NaN or -inf, which silently blanks the axis. The divide-by-zero
            # that produces the -inf is the case being detected, so it is not worth warning about.
            with np.errstate(divide='ignore'):
                limits = np.log10(np.abs([lower, upper]))

            lower, upper = (limits if np.all(np.isfinite(limits)) else (None, None))

    ax.clear()

    if vertical:
        ax.plot(values, distance)
        ax.invert_yaxis()
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.set_xlabel(value_label)
        ax.set_ylabel(space_label)

        if lower is not None:
            ax.set_xlim(lower, upper)
    else:
        ax.plot(distance, values)
        # Put the x axis back at the bottom explicitly. clear() restores the label but leaves the
        # tick marks on the top spine, so switching back from the depth view would otherwise keep
        # ticks up there.
        ax.xaxis.tick_bottom()
        ax.xaxis.set_label_position('bottom')
        ax.set_xlabel(space_label)
        ax.set_ylabel(value_label)

        if lower is not None:
            ax.set_ylim(lower, upper)


def _is_spatial(path):
    """Whether a TecPlot file holds a field over space rather than a record through time.

    Decided by reading the header rather than by listing which extensions are which: MIN3P has some
    thirty output categories and both families are TecPlot, but a spatial file names x, y and z as
    its first columns where a breakthrough file leads with `time` (or `pH` for a pC-pH run).
    """
    try:
        with open(path, errors='replace') as f:
            f.readline()
            headers = [name.strip().strip('"').lower()
                       for name in re.split(r'"\s*,\s*"', f.readline().split('=', 1)[-1])]
    except (OSError, IndexError):
        return False

    return headers[:1] == ['x']


def _min3p_run_name(directory):
    """The run name MIN3P records in root.dat, or None where this is not a MIN3P directory."""
    root = pathlib.Path(directory) / 'root.dat'

    if not root.is_file():
        return None

    text = root.read_text(errors='replace').strip()

    return text.split()[0] if text else None


def data_cats(directory):
    """The spatial output categories in a run directory, and how many snapshots each has.

    Reads either code's output. CrunchTope writes `{quantity}{n}.tec`; MIN3P writes
    `{run}_{n}.{quantity}` and says what the run is called in root.dat.
    """
    global _directory, _simulator, _run_name, _snapshots, _files
    _directory = directory
    _files = {}
    _run_name = _min3p_run_name(directory)
    path = pathlib.Path(directory)
    _simulator = 'min3p' if _run_name and not any(path.glob('*.tec')) else 'crunchtope'

    if _simulator == 'min3p':
        # Group by extension, and keep only the spatial families: the breakthrough and batch
        # output is a time series at a point and has no profile to draw.
        found = {}

        for file in path.glob(f'{_run_name}_*'):
            index = re.fullmatch(rf'{re.escape(_run_name)}_(\d+)', file.stem)

            if index and file.suffix:
                category = file.suffix.lstrip('.')
                found.setdefault(category, []).append(int(index.group(1)))
                _files[(category, int(index.group(1)))] = file

        spatial = {cat: sorted(indices) for cat, indices in found.items()
                   if _is_spatial(path / f'{_run_name}_{sorted(indices)[0]}.{cat}')}

        if not spatial:
            raise FileNotFoundError(f'no spatial MIN3P output for run {_run_name!r} in {directory}')

        _snapshots = spatial
        # The commonest count, not the smallest. MIN3P writes some categories once however many
        # snapshots the rest get -- the velocity field is written at the start and left -- and the
        # minimum would drag the whole browser down to that one. The browser re-reads the count
        # per category anyway, so this is only the opening value.
        counts = sorted(len(indices) for indices in spatial.values())

        return set(spatial), max(set(counts), key=counts.count)

    # Take the file name, drop the extension, then drop the trailing output index. A regex on the
    # stem rather than rstrip, which strips any of the given characters rather than a suffix:
    # 'rate.tec'.rstrip('.tec') is 'ra'. This matches core.file_methods in Omphalos, which reads
    # the same filenames.
    found = {}

    for file in path.glob('*.tec'):
        # Split the stem into the quantity and its snapshot number. A file with no number is a
        # single output rather than a series -- 'totconND.tec' is one -- and is treated as
        # snapshot 1, so selecting it browses the one snapshot it has instead of looking for a
        # 'totconND1.tec' that was never written.
        category, digits = re.fullmatch(r'(.*?)(\d*)', file.stem).groups()
        index = int(digits) if digits else 1
        found.setdefault(category, []).append(index)
        _files[(category, index)] = file

    f_set = set(found)

    if not f_set:
        raise FileNotFoundError(
            f'no CrunchTope .tec output and no MIN3P root.dat in {directory} -- point this at a '
            f'run directory, or at a CrunchTope deck sitting beside its output')

    _snapshots = {cat: sorted(indices) for cat, indices in found.items()}
    counts = sorted(len(indices) for indices in found.values())

    return f_set, max(set(counts), key=counts.count)


def box_plot(file_cat, plot_var, max_time):
    """Plot out the time series for the file category in a box model (i.e. 0D CT model)."""
    import numpy as np

    indices = snapshot_indices(file_cat) or list(range(1, max_time + 1))
    series = np.empty(len(indices))

    try:
        for position, index in enumerate(indices):
            df, column_headers = read_tecplot(file_cat, index)
            series[position] = df[plot_var]
    except KeyError:
        return

    return series


def initialise_box(file_cat):
    df, column_headers = read_tecplot(file_cat, first_snapshot(file_cat))
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df['X'], np.zeros_like(df['X']))

    return fig, ax


def plot_var_range(max_time, file_cat, plot_vars):
    min_list = []
    max_list = []
    for t in snapshot_indices(file_cat) or range(1, max_time + 1):
        df = read_tecplot(file_cat, t)[0]
        arr = df.loc[:, plot_vars].to_numpy()
        min_list.append(arr.min())
        max_list.append(arr.max())

    lower = np.amin(min_list)
    upper = np.amax(max_list)

    return lower, upper


def read_times(path):
    """return a dictionary of lines in a file, with the values as the line numbers.
    will ignore any commented lines in the ct input file, but will still count their line number,
    so line numbers in dictionary will map to the true line number in the file.
    """
    import re

    with open(path, 'r') as f:
        for line_num, line in enumerate(f):
            # input files edited on unix systems have newline characters that must be stripped.
            # also strip any trailing whitespace.
            if line.startswith('spatial_profile'):
                line = line.rstrip('\n ')
                line = re.split(r'\s+', line)
                line.pop(0)
                break
            else:
                pass

        f.close()

        line = [float(x) for x in line]
    return line


def output_times(deck=None, file_cat=None):
    """The simulated time of each snapshot, in output order.

    Where the time is recorded differs by code. CrunchTope states its output times in the deck, on
    the `spatial_profile` line, and puts nothing usable in the `.tec` files of an older build --
    hence `deck`. MIN3P writes no such list, but does stamp each snapshot on its TecPlot zone line,
    so the times are read back off the output itself.

    Args:
        deck: The CrunchTope input deck. Ignored for MIN3P, which does not need it.
        file_cat: Which category to read the MIN3P times from. Any spatial one will do, since they
            are written together; defaults to whichever comes first.

    Returns:
        A list of times, or an empty list where the run records none.
    """
    if _simulator != 'min3p':
        return read_times(deck) if deck is not None else []

    # The fullest record, since categories need not be written together and the times should be
    # every time the run reported, not just the ones the sparsest category happened to catch.
    file_cat = file_cat or max(sorted(_snapshots), key=lambda cat: len(_snapshots[cat]))
    found = []

    for index in _snapshots.get(file_cat, []):
        with open(_output_path(file_cat, index), errors='replace') as f:
            f.readline()
            f.readline()
            stamp = _ZONE_TIME.search(f.readline())

        # Fortran writes an exponent as D as readily as E, and float() only knows the latter.
        found.append(float(stamp.group(1).replace('D', 'E').replace('d', 'e')) if stamp else np.nan)

    return found


def simulator():
    """Which code wrote the run currently open, as 'crunchtope' or 'min3p'."""
    return _simulator


def snapshot_indices(file_cat):
    """The snapshot numbers one category actually has, in order.

    Not always 1..N. MIN3P numbers from 0, where snapshot 0 is the initial state -- written before
    the run starts, and stamped 'initial' rather than with a time. CrunchTope numbers from 1. A
    slider ranged over the wrong one either misses the initial state or runs off the end.
    """
    return list(_snapshots.get(file_cat, []))


def snapshot_count(file_cat, default=None):
    """How many snapshots one output category has.

    CrunchTope writes every category at every output time, so the count is the same for all of them.
    MIN3P does not: the velocity field is written once and the chemistry many times, so a slider
    ranged over the chemistry runs off the end of the velocity.
    """
    indices = _snapshots.get(file_cat)

    return len(indices) if indices is not None else default


def open_run(path):
    """Point topepan at one run, given either its output directory or its CrunchTope deck.

    A deck is accepted because CrunchTope keeps the output times there and nowhere else, so the one
    path gives both the output and the times. MIN3P stamps its own output, so its directory is
    enough.

    Returns:
        (categories, snapshots, times) -- categories sorted, and times empty where none are
        recorded.
    """
    path = pathlib.Path(path)
    directory = path if path.is_dir() else path.parent
    categories, snapshots = data_cats(directory)

    return sorted(categories), snapshots, output_times(None if path.is_dir() else path)


def profile_axis(data_frame):
    """Which spatial axis a 1-D profile should be drawn along.

    Whichever of X, Y, Z actually varies. A column may run down any of them -- MIN3P's dissolution
    benchmark is a Z column with X singleton -- and plotting against a constant draws a vertical
    line where a profile should be.
    """
    present = [name for name in ('X', 'Y', 'Z') if name in data_frame]
    varying = [name for name in present if data_frame[name].nunique() > 1]

    return next(iter(varying or present), 'X')


