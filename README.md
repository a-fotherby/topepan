# Topepan
A Jupyter notebook environment for exploring and analysing CrunchTope data.

![](https://images.unsplash.com/photo-1553126541-200d71db66f9?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2938&q=80)

### Installation

1. Ensure conda-forge is enabled: https://conda-forge.org/
2. Run the following:
   1. `conda env create --file requirements.yml`
3. Launch your Jupyter client of choice.
   1. Change the python kernel being used is `topepan`.

### Usage

1. Pick a geometry that matches the geometry of your output data.
2. Add the path to the CrunchTope input file to `topepan/config.py`.
3. Run the Jupyter notebook.

### Geometries

+ Box model (0D): `box.ipynb`
  + Plots a time series of your box model state.
+ Column (1D): `column.ipynb`
  + Plots your depth profile, with a time slider to move through your profile snapshots.

### Troubleshooting
+ You may also need `nb_conda_kernels` installed in you `base` conda prefix to make the `topepan` kernel accessible. 
+ You many have to change the GUI toolkit specified by `%matplotlib` line to fit your system. Other options include:
  + `ipympl`
  + `osx`
  + `notebook`

&copy; Angus Fotherby (2019 - 2022). All rights reserved.