# COVID-19 Data Analysis

Basic modeling with Real-World Data.

<img src="figures/survival_by_age.png" alt="Violin plot demonstrating that COVID survival correlates with age at time of hospitalization." width="500px" />

Author: [Zachary Levonian](https://github.com/levon003)

### Structure

A good entrypoint to the analyisis is [the Jupyter notebook that explores the dataset](/notebook/DataExploration.ipynb) or [the Jupyter notebook that analyses the data by fitting multiple logistic regression models](/notebook/DataModeling.ipynb).

Otherwise, the directory layout is:

- `notebook` contains the analysis notebooks.
- `src` contains the `covid_modeling` Python package with helper functions and classes to support the analysis.
- `tests` contains `pytest` tests for the `covid_modeling` package.
- `data` is presumed to be the location of the input data... see the Data section below for more details.
- `figures` contains any images produced within the analysis notebooks.

### Data

The data is a representative but fabricated sample of research data provided by [ConcertAI](https://www.concertai.com/). I don't have permission to share it publicly. Note that all PII is random in the data (e.g. names and addresses are random).

The structure of the data is visible in the analysis notebooks, and a sample is contained in the test resources (`tests/resources/`).

### Installation

This repository uses `poetry` as its package manager, coordinated by `make`.

To install `poetry` and needed dependencies, run `make install`.

To run tests, run `make test`.

A few useful commands:

 - `poetry run <command>` - Run the given command, e.g. `poetry run pytest` invokes the tests.
 - `source $(poetry env info --path)/bin/activate` - An alternative to `poetry shell` that's less buggy in conda environments.
