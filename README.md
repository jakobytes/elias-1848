# ELIAS 1848 pipeline

This repository contains a set of scripts for creating the corpus and
database used ELIAS 1848. It is a modification of the
pipeline, database creation, and web-interface used in the
[FILTER project](https://blogs.helsinki.fi/filter-project/).
The corpus is a compilation of three folk poetry collections that
are made publicly available by the [Finnish Literature Society on
GitHub](https://github.com/sks190).

The pipeline reads a set of XML-files and produces a set of tables 
in CSV-format, to be processed into a database in a later step.

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
- Modified metadata in literary sources for "Elias Lönnrot : Lisiä Vanhaan Kalevalaan"
  published in 1895 by A.R. Niemi in data/raw/kr/kr01-53.xml.
  Apart from the introduction it consists of poems recorded before 1848.
  These are at the moment (31.12.2024) wrongly annotated in the metadata.
- Filtered the corpus by XML-metadata using filter_by_year.py to filter by
  attribute "y" (year) in tag in <ITEM> to only include items where y < 1849.
  The processed files are created in data/work/filtered.
- Run lonnrot_exceptions.py on data/raw/kr/kr01-53.xml to include the following in the
  final corpus. They consist of material that E. Lönnrot had in 1948 but were
  published by him at a later date. (COPIED THE OUTPUT MANUALLY to data/work/filtered/kr)
  - Kalevala (1849)
  - Elias Lönnrot : Suomen Kansan arwoituksia ynnä 189 Wiron arwoituksen kanssa (1851)
  - Suomen Kansan Muinaisia Loitsurunoja toimittanut Elias Lönnrot (1880)

## Installation and running

NOTE TO SELF: The "sed" command used in the Makefile is for gnu-sed. *Macs run
on BSDLinux* and use a different flavour of sed, which is *incompatible* 
with the script in the Makefile. It is possible to switch to using gnu-sed on
Mac, but I ended up running it on a Linux-VM for convenience.

After cloning this repository, initialise the Git submodules for the
source data using the command:
```
git submodule update --init --recursive
```
<del> CURRENTLY THE MODIFIED kr01-53.xml MUST BE COPIED MANUALLY TO REPLACE
THE VERSION IN data/raw/kr. ALSO MANUALLY DELETE kalevipoeg.xml.
THIS WILL BE AUTOMATED ONCE I'M SURE THAT STUFF WORK AS INTENDED.</del>

Further, install the Python dependencies. The preferred way of doing it
is through Anaconda; use the environment file `env.yml`. Unless you
REALLY wan't to know the underpinnings of installed packages in your OS, just do it.

The different steps of the pipeline are called using GNU Make. The
environment variable `DATA_DIR` should be set to the path of the output
directory (which will contain the resulting CSV files). For example to
call the preprocessing, execute:
```
DATA_DIR=/path/to/filter-data make combined
```
Alternatively you can create environment variables in your OS e.g.
"export DATA_DIR=/path/to/filter-data" or, even better, add it to
the Conda environment with "conda env convig vars set DATA_DIR=/path/to/filter-data".
As these differ from user and case, I decided against hardcoding these.

Also the tool *jq* for processing json-files is currently missing from the
environment. It must be installed separately using your package manager of choice.

## Steps

### Sources and preprocessing

Execute `make combined` to run the preprocessing step.

The corpus consists of four collections, which are linked as submodules in
`data/raw`:
* [Suomen Kansan Vanhat Runot (SKVR)](https://github.com/sks190/SKVR) (public)
* [Julkaisemattomat Runot (JR)](https://github.com/sks190/jr) (public)
* [Kirjalliset Runot (KR)](https://github.com/sks190/kr_FILTER) (public)

A description of the format of the source files can be found [here](./data/raw/README.md).

### Similarity computation

To compute similarity and clustering for the new corpus, one must run some Makefile targets
manually. The calculations are optimised for GPU-processing and require some
calculation power. Running without GPU is possible but requires modifications in
processing and is not covered here.

### Other scripts

The file runoregi_pages.tsv needs to be created manually with "make $DATA_DIR/runoregi_pages.tsv".
It creates a table of text-data for the runoregi-interface.


## Copyright note

The code published in this repository is licensed under the MIT license. The creator(s) and
hosts of the original code and text-corpora must be duly credited. The code here isn't made
to harm you or your computer in any way, but any responsibility of running this code is
yours. Assessing the consequences is the users responsibility.

For the folk poetry materials linked as submodules, see the information
in their repositories.
