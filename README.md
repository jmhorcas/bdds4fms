# Binary Decision Diagrams for feature models in the Universal Variability Language
This repository contains the scripts to build the dataset BDDs derived from feature models expressed in UVL from the [FM Benchmark dataset](https://doi.org/10.1145/3646548.3672590). 

## How to use it
Here we explain how to build the BDD for a set of feature models in UVL.

### Requirements
We relies on [flamapy](https://flamapy.github.io/) to work with the feature models in UVL.
In particular, the main dependencies are:

- Linux is required.
- [Python 3.11+](https://www.python.org/)
- [Flamapy](https://flamapy.github.io/)


### Download and installation
1. Install [Python 3.11+](https://www.python.org/)
2. Download/Clone this repository and enter into the main directory.

    `git clone https://github.com/jmhorcas/bdds4fms.git`

    `cd bdds4fms`

3. Create a virtual environment: `python -m venv env`
4. Activate the environment: `source env/bin/activate`
5. Install dependencies (flamapy): `pip install flamapy`

### Download the 

### Execution of the scripts

``python uvl2bdd.py [<feature_model.uvl> | <uvl_dataset_dir>]`

The script receives as input a feature model in UVL or a directory with UVL models.
It generates the symbolic representation in a `logic/` folder, and the BDD files in a `bdd/` folder.

Additionally, it creates a `results.csv` file with statistics about the process such as execution time and sizes of the models.

A `.log` file is also generated with debug information in case of any error.
