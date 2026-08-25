import pathlib
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

_directory = None


def read_tecplot(file_cat, file_num):
    if _directory is not None:
        file_name = str(pathlib.Path(_directory) / f'{file_cat}{file_num}.tec')
    else:
        file_name = f'{file_cat}{file_num}.tec'
    with open(file_name) as f:
        f.readline()
        header_line = f.readline()
        headers = header_line.split('"')
        column_headers = []
        for string in headers:
            if not string.isspace():
                column_headers.append(string)
        column_headers = column_headers[1:]
        df = pd.read_csv(file_name, sep=' ', skipinitialspace=True, skiprows=[0, 1, 2], names=column_headers)
        df = df.replace(r'(\d)-(\d)', r'\1e-\2', regex=True)
        df = df.replace(r'Ee', 'e', regex=True)
        for i in column_headers:
            try:
                df[i] = pd.to_numeric(df[i], downcast="float")
            except:
                print(f'Error with {i}')

        return df, column_headers


def tecplot_2d(data_frame, scalar_name, vmin, vmax):
    z = data_frame.pivot('Y', 'X', scalar_name)
    x, y = np.meshgrid(z.columns.values, z.index.values)
    levels = np.linspace(vmin, vmax, 16)
    CS = plt.contourf(x, y, z, levels=levels, cmap=cm.viridis, extend='both')

    colour_bar = plt.colorbar(CS)
    plt.xlabel('y / m')
    plt.ylabel('x / m')
    plt.show()


def initialise1D(file_cat, vertical=True):
    """Set up an empty 1-D profile.

    Args:
        vertical: Depth convention -- distance down the y axis, value across the top. This is how
            the column browser has always drawn, and stays the default. False puts distance on the
            x axis instead, which reads better for a flow path than for a depth.
    """
    df, column_headers = read_tecplot(file_cat, 1)
    fig, ax = plt.subplots(figsize=(9, 6))
    zeros = np.zeros_like(df['X'])
    line, = ax.plot(*((zeros, df['X']) if vertical else (df['X'], zeros)))

    if vertical:
        ax.invert_yaxis()
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')

    ax.set_ylabel('X' if vertical else '')
    ax.set_xlabel('' if vertical else 'X')

    return fig, ax, line


def draw_profile(ax, distance, values, vertical=True, lower=None, upper=None, value_label=''):
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
        value_label: Labels the value axis; the spatial axis is labelled 'X'.
    """
    ax.clear()

    if vertical:
        ax.plot(values, distance)
        ax.invert_yaxis()
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.set_xlabel(value_label)
        ax.set_ylabel('X')

        if lower is not None:
            ax.set_xlim(lower, upper)
    else:
        ax.plot(distance, values)
        # Put the x axis back at the bottom explicitly. clear() restores the label but leaves the
        # tick marks on the top spine, so switching back from the depth view would otherwise keep
        # ticks up there.
        ax.xaxis.tick_bottom()
        ax.xaxis.set_label_position('bottom')
        ax.set_xlabel('X')
        ax.set_ylabel(value_label)

        if lower is not None:
            ax.set_ylim(lower, upper)


def data_cats(directory):
    global _directory
    _directory = directory
    # Take the file name, drop the extension, then drop the trailing output index. A regex on the
    # stem rather than rstrip, which strips any of the given characters rather than a suffix:
    # 'rate.tec'.rstrip('.tec') is 'ra'. This matches core.file_methods in Omphalos, which reads
    # the same filenames.
    f_list = [re.sub(r'\d+$', '', p.stem) for p in pathlib.Path(directory).glob('*.tec')]
    f_set = set(f_list)
    output_total = len(f_list) / len(f_set)
    return f_set, int(output_total)


def box_plot(file_cat, plot_var, max_time):
    """Plot out the time series for the file category in a box model (i.e. 0D CT model)."""
    import numpy as np

    series = np.empty(max_time)
    try:
        for i in np.arange(0, max_time):
            df, column_headers = read_tecplot(file_cat, i + 1)
            series[i] = df[plot_var]
    except KeyError:
        return

    return series


def initialise_box(file_cat):
    df, column_headers = read_tecplot(file_cat, 1)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df['X'], np.zeros_like(df['X']))

    return fig, ax


def time_nav(file_cat, time, plot_var, max_time):
    df, column_headers = read_tecplot(file_cat, time)
    vmin, vmax = plot_var_range(max_time, file_cat, plot_var)
    tecplot_2d(df, plot_var, vmin, vmax)


def time_nav_1d(file_cat, time, plot_var, max_time):
    df, column_headers = read_tecplot(file_cat, time)
    lims = plot_var_range(max_time, file_cat, plot_var)
    tecplot_1d(df, plot_var, lims)


def plot_var_range(max_time, file_cat, plot_vars):
    min_list = []
    max_list = []
    for t in range(1, max_time + 1):
        df = read_tecplot(file_cat, t)[0]
        arr = df.loc[:, plot_vars].to_numpy()
        min_list.append(arr.min())
        max_list.append(arr.max())

    lower = np.amin(min_list)
    upper = np.amax(max_list)

    return lower, upper


def import_time_series(file_name):
    with open(file_name) as f:
        f.readline()
        header_line = f.readline()
    column_headers = header_line[11:]
    column_headers = column_headers.replace("'", "")
    column_headers = column_headers.replace('"', "")
    column_headers = column_headers.replace('(days)', "")
    column_headers = column_headers.replace(' ', "")
    column_headers = column_headers.rstrip('\n')
    column_headers = column_headers.rstrip(',')
    column_headers = column_headers.split(',')
    print(column_headers)

    df = pd.read_csv(file_name, engine='python', sep='\s+', skiprows=[0, 1])
    df.columns = column_headers
    return df, column_headers


def breakthrough(time, plot_var, data_frame):
    fig, ax = plt.subplots()
    ax.plot(time, data_frame.loc[:, plot_var])
    return fig, ax


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
                line = re.split('\s+', line)
                line.pop(0)
                break
            else:
                pass

        f.close()

        line = [float(x) for x in line]
    return line