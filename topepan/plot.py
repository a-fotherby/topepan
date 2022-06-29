import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
from glob import glob


def read_tecplot(file_cat, file_num):
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
        df = df.replace('-', 'e-', regex=True)
        df = df.replace('Ee', 'e', regex=True)
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


def initialise1D(file_cat):
    df, column_headers = read_tecplot(file_cat, 1)
    fig, ax = plt.subplots(figsize=(9, 6))
    line, = ax.plot(df['X'], np.zeros_like(df['X']))
    return fig, ax, line


def data_cats(directory):
    os.chdir(directory)
    f_list = glob('*.tec')
    f_list = [i.rstrip('.tec') for i in f_list]
    f_list = [i.rstrip('0123456789') for i in f_list]
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
