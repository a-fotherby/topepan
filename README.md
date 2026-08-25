# Topepan

<p align="center">
  <strong>A Jupyter environment for exploring CrunchTope output and Omphalos sweeps</strong>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#notebooks">Notebooks</a> •
  <a href="#troubleshooting">Troubleshooting</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/CrunchTope-supported-orange" alt="CrunchTope">
  <img src="https://img.shields.io/badge/Omphalos-sweeps-orange" alt="Omphalos">
</p>

---

## Installation

```bash
conda env create --file requirements.yml
conda activate topepan
jupyter lab
```

**Launch Jupyter from this environment.** The widget frontend has to live in the environment that
*serves* Jupyter, not merely the one providing the kernel — see [Troubleshooting](#troubleshooting).

---

## Usage

Pick the notebook matching the shape of your output, set the run folder in the notebook itself, and
work through it. There is no configuration file to edit first: the folder you are browsing changes
several times a session, so it is a widget in the notebook rather than a setting somewhere else.

---

## Notebooks

| Notebook | Reads | What it does |
|---|---|---|
| `box.ipynb` | one run, 0-D | Time series of a box model's state |
| `column.ipynb` | one run, 1-D | Depth profile with a time slider, and a choice of orientation |
| `sweep.ipynb` | an Omphalos sweep | Every run of a sweep at once, compared across whatever was varied |

### Browsing one run — `box.ipynb`, `column.ipynb`

These read CrunchTope's `.tec` output directly. Type the run folder into the **Run folder** box and
the output types, variables and time steps refresh to match, so switching between runs needs no code
edit and no kernel restart.

`column.ipynb` draws either way round. **X on the y axis** is the depth convention — distance
downwards, value across the top — and **X on the x axis** reads better for a flow path. Both are
useful for a 1-D column, so it is a toggle rather than a decision baked into the notebook.

### Browsing a sweep — `sweep.ipynb`

A sweep is many runs that differ in whatever was varied, and it is read through Omphalos's `coeus`
package rather than from `.tec` files: point it at a `results.nc` and it finds `conditions.nc`
alongside.

This is the one notebook that needs something outside topepan. It finds Omphalos in this order, so
on a machine where the two sit side by side there is nothing to configure:

1. `coeus` already importable — e.g. `pip install -e /path/to/Omphalos` into this environment
2. the `OMPHALOS_DIR` environment variable
3. an `Omphalos` directory beside wherever the notebook is running, the usual layout

If none of those find it, the notebook says so and names the two ways to fix it rather than failing
on an import several cells later.

The run axis is drawn **whole** — every plot shows all the runs at once and the widgets choose which
variable to look at, not which run. Stepping through runs one at a time would hide the comparison the
sweep was run to make. The 2-D map is the exception, since it can only show one run.

Start with `describe()`, which says how many runs there are, what was varied, and whether the runs
actually finished. A sweep whose runs time out still writes a `results.nc` full of plausible numbers.

Every widget in `sweep.ipynb` does nothing but call a function from `coeus.sweep_plots`, so if the
widget stack misbehaves you can call those directly and lose the sliders rather than the analysis.

---

## Troubleshooting

**A widget prints as `IntSlider(value=0, ...)` instead of appearing.** The kernel built the widget
and the frontend had nothing to draw it with. The widget JavaScript must be installed in the
environment **serving** Jupyter, not the one providing the kernel — so a server launched from a bare
`base` environment cannot render widgets from any kernel, however well equipped that kernel is. Check
with:

```bash
jupyter labextension list      # look for @jupyter-widgets/jupyterlab-manager
```

If it is missing, launch Jupyter from this environment instead, or install `jupyterlab_widgets`
where you launch it from.

**The `topepan` kernel is not offered.** `nb_conda_kernels` has to be installed in the environment
Jupyter is served from for it to see kernels in other environments.

**Figures are static, or `%matplotlib ipympl` fails.** `ipympl` is missing. Other backends worth
trying are `osx` and `notebook`, though the notebooks assume `ipympl`.

---

## License

MIT License

Copyright © Angus Fotherby & Harold Bradbury (2019-2026)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
