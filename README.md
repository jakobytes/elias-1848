# ELIAS 1848 pipeline

This repository contains a set of scripts for creating the corpus and
database used ELIAS 1848. It is a modification of the
pipeline, database creation, and web-interface used in the
[FILTER project](https://blogs.helsinki.fi/filter-project/).
The corpus is a compilation of three folk poetry collections,that
are made publicly available by the [Finnish Litterature Society on
GitHub](https://github.com/sks190).

The aim of this project is to harness the tools created by [Maciej
Janicki](https://github.com/maciejjan) to analyse a subset of the
corpus used in the FILTER project. The subset consists of the
poems recorded before the publication of Kalevala in 1849 to
reveal how Elias Lönnrot processed the collected poems he had access
to when composing the Kalevala epic. The number of recorded poems
before 1849 in the database is 21919. This is roughly 10% of the 
original dataset.

The modifications to create the subset are as follows:
- Removed the Estonian poem corpus by:
  - dropping the ERAB corpus submodule from the pipeline.
  [Estonian poems from Eesti regilaulude](https://github.com/rahvaluule/erab)
  - dropping Kalevipoeg from literary sources (KR)
korjattu "Lisiä vanhaan Kalevalaan" vuodeksi 1848
tämän jälkeen rajattu korpus metatietojen perusteella y<1849
rajattuun aineistoon lisätty poikkeukset: Kalevala, Loitsut, Sananlaskut
ajettu uusi korpus filter-pipelinen läpi ja laskettu uudet similariteeti ja klusterointiarvot


The pipeline reads a set of XML-files and produces a set of tables 
in CSV format to be processed into a database in a later step.

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
