import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
from glob import glob

def read_tecplot(file_cat, file_num):
    file_name = '{}{}.tec'.format(file_cat, file_num)
    with open(file_name) as f:
        f.readline()
        header_line = f.readline()
        column_headers = header_line.split()
        column_headers = column_headers[2:]
        for i in column_headers:
            column_headers[column_headers.index(i)] = i.replace('"', '')
                
        df = pd.read_csv(file_name, sep=' ', skipinitialspace=True, skiprows=[0,1,2], names=column_headers)
        
        return df, column_headers

def tecplot_2d(data_frame, scalar_name, vmin, vmax):
    z = data_frame.pivot('Y', 'X', scalar_name)
    x, y = np.meshgrid(z.columns.values, z.index.values)
    levels = np.linspace(vmin, vmax, 16)
    CS = plt.contourf(x, y, z, levels=levels, cmap=cm.viridis, extend='both')

    colorbar = plt.colorbar(CS)
    plt.xlabel('y / m')
    plt.ylabel('x / m')
    plt.show()
    
def tecplot_1d(data_frame, scalar_name, lims):
    lower, upper = lims
    fig, ax = plt.subplots(figsize=(9,6))
    ax.plot(data_frame['X'], data_frame[scalar_name])
    
    if upper > 0:
        upper = upper * 1.02
    elif upper < 0: 
        upper = upper * 0.98
    else:
        upper = -lower
    
    if lower > 0:
        lower = lower * 0.98
    elif lower < 0:
        lower = lower * 1.02
    else:
        lower = -upper
        
    print(upper, lower)
    ax.set_ylim(lower, upper)
    
    
def data_cats(directory):
    os.chdir(directory)
    f_list = glob('*.tec')
    f_list = [i.rstrip('.tec') for i in f_list]
    f_list = [i.rstrip('0123456789') for i in f_list]
    f_set = set(f_list)
    output_total = len(f_list) / len(f_set)
    return f_set, int(output_total)

def time_nav(file_cat, time, plot_var, max_time):
    df, column_headers = read_tecplot(file_cat, time)
    vmin, vmax = color_map_range(max_time, file_cat, plot_var)
    tecplot_2d(df, plot_var, vmin, vmax)
    
def time_nav_1d(file_cat, time, plot_var, max_time):
    df, column_headers = read_tecplot(file_cat, time)
    lims = plot_var_range(max_time, file_cat, plot_var)
    tecplot_1d(df, plot_var, lims)    
    
def plot_var_range(max_time, file_cat, plot_var):
    min_list = []
    max_list = []
    for t in range(1, max_time+1):
        df = read_tecplot(file_cat, t)[0]
        s = df.loc[:, plot_var]
        min_list.append(s.nsmallest(1).values)
        max_list.append(s.nlargest(1).values)    
        
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
    
    df = pd.read_csv(file_name, engine='python', sep='\s+', skiprows=[0,1]) 
    df.columns=column_headers
    return df, column_headers

def breakthrough(time, plot_var, data_frame):
    fig, ax = plt.subplots()
    ax.plot(time, data_frame.loc[:, plot_var])
    return fig, ax