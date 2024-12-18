# FILTER pipeline

This repository contains a set of scripts for creating the corpus and
database used in the [FILTER project](https://blogs.helsinki.fi/filter-project/).
The corpus is a compilation of four folk poetry collections, of which
at the moment two are public and two non-public.
The pipeline produces a set of tables in CSV format that is stored in
[hsci-r/filter-data](https://github.com/hsci-r/filter-data).

## Installation and running

After cloning this repository, initialize the Git submodules for the
source data using the command:
```
git submodule update --init --recursive
```

Further, install the Python dependencies. The preferred way of doing it
is through Anaconda - use the environment file `env.yml`. For CSC
computing clusters, it is recommended to use
[Tykkky](https://docs.csc.fi/computing/containers/tykky/).

The different steps of the pipeline are called using GNU Make. The
environment variable `DATA_DIR` should be set to the path of the output
directory (which will contain the resulting CSV files). For example to
call the preprocessing, execute:
```
DATA_DIR=/path/to/filter-data make combined
```

## Steps

### Sources and preprocessing

Execute `make combined` to run the preprocessing step.

The corpus consists of four collections, which are linked as submodules in
`data/raw`:
* [Suomen Kansan Vanhat Runot (SKVR)](https://github.com/sks190/SKVR) (public)
* [Eesti Regilaulude Andmebaas (ERAB)](https://github.com/rahvaluule/erab) (public)
* [Julkaisemattomat Runot (JR)](https://github.com/sks190/jr) (private)
* [Kirjalliset Runot (KR)](https://github.com/sks190/kr_FILTER) (private)

The private repositories are planned to be published soon, but currently
the pipeline can also be executed without them.

A description of the format of the source files can be found [here](./data/raw/README.md).

### Similarity computation

TODO

### Other scripts

TODO

## Copyright note

The code published in this repository is licenced under the MIT license.

For the folk poetry materials linked as submodules, see the information
in their repositories.
