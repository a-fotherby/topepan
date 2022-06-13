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
        headerLine = f.readline()
        headers=headerLine.split('"')
        columnHeaders=[]
        for string in headers:
            if string.isspace() == False:
                columnHeaders.append(string)
        columnHeaders=columnHeaders[1:]   
        df = pd.read_csv(file_name, sep=' ', skipinitialspace=True, skiprows=[0,1,2], names=columnHeaders)
        df = df.replace('-','e-', regex=True)
        df = df.replace('Ee','e', regex=True)
        for i in columnHeaders:
            df[i] = pd.to_numeric(df[i], downcast="float")
        
        return df, columnHeaders

def tecplot_2d(data_frame, scalar_name, vmin, vmax):
    z = data_frame.pivot('Y', 'X', scalar_name)
    x, y = np.meshgrid(z.columns.values, z.index.values)
    levels = np.linspace(vmin, vmax, 16)
    CS = plt.contourf(x, y, z, levels=levels, cmap=cm.viridis, extend='both')

    colorbar = plt.colorbar(CS)
    plt.xlabel('y / m')
    plt.ylabel('x / m')
    plt.show()
    
def initialise1D(file_cat, lims=(-1,1)):
    df, column_headers = read_tecplot(file_cat, 1)
    fig, ax = plt.subplots(figsize=(9,6))
    line, = ax.plot(np.zeros_like(df['X']),df['X'])
    return fig, ax, line
    
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
    vmin, vmax = plot_var_range(max_time, file_cat, plot_var)
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
        s = pd.to_numeric(df.loc[:, plot_var], errors='coerce')
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