# Topepan

<p align="center">
  <strong>A Jupyter environment for exploring CrunchTope and MIN3P output, and
  <a href="https://github.com/a-fotherby/Omphalos">Omphalos</a> sweeps</strong>
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
  <img src="https://img.shields.io/badge/MIN3P-supported-orange" alt="MIN3P">
  <a href="https://github.com/a-fotherby/Omphalos"><img src="https://img.shields.io/badge/Omphalos-sweeps-orange" alt="Omphalos"></a>
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

This environment also carries what Omphalos needs to run, so one `conda env create` covers both
running sweeps and browsing them. Omphalos's own `requirements.yml` deliberately omits the notebook
and plotting stack so it stays installable on a headless cluster.

---

## Usage

Pick the notebook matching the shape of your output, edit the path at the top of it, and work
through it. There is no configuration file to set up first: the run you are looking at changes
several times a session, so it is a plain assignment in the notebook you already have open, where
your editor can complete the path for you.

The committed notebooks carry a placeholder path, so the first thing to do in a fresh checkout is
point it at a real run.

---

## Notebooks

| Notebook | Reads | What it does |
|---|---|---|
| `box.ipynb` | one run, 0-D | Time series of a box model's state |
| `column.ipynb` | one run, 1-D | Depth profile with a snapshot slider, and a choice of orientation |
| `sweep.ipynb` | an Omphalos sweep | Every run of a sweep at once, compared across whatever was varied |

### Browsing one run — `box.ipynb`, `column.ipynb`

These read the output files directly — CrunchTope's `.tec` or MIN3P's `.gs*`, whichever the folder
holds. Give either the run directory or the CrunchTope deck: CrunchTope states its output times in
the deck and nowhere else, so passing the deck gets the times as well as the output beside it, while
MIN3P stamps each snapshot itself and needs only the directory. Edit the path and re-run from that
cell down.

Snapshot numbering differs and the notebooks follow whatever is actually on disk: CrunchTope numbers
from 1, MIN3P from 0 with snapshot 0 the initial state, and MIN3P writes the flow field far fewer
times than the chemistry, so the slider is re-ranged per output type.

`column.ipynb` draws either way round. **Distance on the y axis** is the depth convention — distance
downwards, value across the top — and **distance on the x axis** reads better for a flow path. Both
are useful for a 1-D column, so it is a toggle rather than a decision baked into the notebook. The
profile follows whichever axis actually varies, so a column running down Z is drawn along Z.

### Browsing a sweep — `sweep.ipynb`

A sweep is many runs that differ in whatever was varied, and it is read through the `coeus` package
of [Omphalos](https://github.com/a-fotherby/Omphalos) rather than from `.tec` files: point it at a
`results.nc` and it finds `conditions.nc` alongside.

**CrunchTope or MIN3P**, without being told which. The two disagree about what to call things —
CrunchTope has `X`/`Y`/`Z` and a `time`, MIN3P has `x`/`y`/`z` and counts snapshots by `output` — so
groups and axes are found by shape rather than by name, and a column running down `z` is profiled
along `z`. A MIN3P sweep writes no `conditions.nc`; what varied is recovered from `records.pkl` by
diffing the decks against each other.

This is the one notebook that needs something outside topepan. It finds Omphalos in this order, so
on a machine where the two sit side by side there is nothing to configure:

1. `coeus` already importable — e.g. `pip install -e /path/to/Omphalos` into this environment
   ([clone it here](https://github.com/a-fotherby/Omphalos))
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
