import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
from glob import glob

def readTecFile(fileCat, fileNum):
    fileName = '{}{}.tec'.format(fileCat, fileNum)
    with open(fileName) as f:
        f.readline()
        headerLine = f.readline()
        columnHeaders = headerLine.split()
        columnHeaders = columnHeaders[2:]
        for i in columnHeaders:
            columnHeaders[columnHeaders.index(i)] = i.replace('"', '')
    
        df = pd.read_csv(fileName, sep=' ', skipinitialspace=True, skiprows=[0,1,2], names=columnHeaders)
    
        return df, columnHeaders

def plot2DTecFile(dataFrame, scalarName, vmin, vmax):
    z = dataFrame.pivot('Y', 'X', scalarName)
    x, y = np.meshgrid(z.columns.values, z.index.values)
    levels = np.linspace(vmin, vmax, 16)
    CS = plt.contourf(x, y, z, levels=levels, cmap=cm.viridis, extend='both')

    colorbar = plt.colorbar(CS)
    plt.xlabel('y / m')
    plt.ylabel('x / m')
    plt.show()
    
def getDataCats(directory):
    os.chdir(directory)
    fList = glob('*.tec')
    fList = [i.rstrip('.tec') for i in fList]
    fList = [i.rstrip('0123456789') for i in fList]
    fSet = set(fList)
    outputTotal = len(fList) / len(fSet)
    return fSet, int(outputTotal)

def plotTimeNav(fileCat, time, plotVar, maxTime):
    df, columnHeaders = readTecFile(fileCat, time)
    vmin, vmax = findColorMapRange(maxTime, fileCat, plotVar)
    plot2DTecFile(df, plotVar, vmin, vmax)
    
def findColorMapRange(maxTime, fileCat, plotVar):
    minList = []
    maxList = []
    for t in range(1, maxTime):
        df = readTecFile(fileCat, t)[0]
        s = df.loc[:, plotVar]
        minList.append(s.nsmallest(1).values)
        maxList.append(s.nlargest(1).values)

    timeSeriesMin = np.amin(minList)
    timeSeriesMax = np.amax(maxList)
    print(timeSeriesMin)
    print(timeSeriesMax)
    
    return timeSeriesMin, timeSeriesMax

def importTimeSeries(fileName):
    with open(fileName) as f:
        f.readline()
        headerLine = f.readline()    
    columnHeaders = headerLine[12:]
    columnHeaders = columnHeaders.replace("'", "")
    columnHeaders = columnHeaders.replace('"', "")
    columnHeaders = columnHeaders.replace('(yrs)', "")
    columnHeaders = columnHeaders.replace(' ', "")
    columnHeaders = columnHeaders.rstrip()
    columnHeaders = columnHeaders.rstrip(',')
    columnHeaders = columnHeaders.split(',')
    
    df = pd.read_csv(fileName, engine='python', sep='\s+', skiprows=[0,1], names=columnHeaders)
    return df, columnHeaders

def plotBreakthrough(time, plotVar, dataFrame):
    fig, ax = plt.subplots()
    ax.plot(time, dataFrame.loc[:, plotVar])