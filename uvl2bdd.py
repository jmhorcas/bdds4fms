import os
import argparse
import pathlib
import logging
from enum import Enum
from typing import Any

import codetiming

from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.fm_metamodel.transformations import UVLReader

import fm2logic
import logic2bdd
from utils.csv_writer import CSVWriter
from utils import utils


logging.basicConfig(filename='uvl2bdd.log', encoding='utf-8', level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)    

TIMEOUT = 7200  # in seconds, 2 hours
TIMEOUT_STR = 'Timeout'
ERROR_STR = 'Error'
CSV_FILE_RESULTS = 'results.csv'
PRECISION = 4


class CSVHeader(Enum):
    MODEL = 'Model'
    FEATURES = 'Features'
    CONSTRAINTS = 'Constraints'
    UVL2LOGIC_TIME = 'UVL2Logic Time (s)'
    VARIABLES = 'Variables'
    CLAUSES = 'Clauses'
    FASTORDER_TIME = 'fastOrder Time (s)'
    LOGIC2BDD_TIME = 'Logic2BDD Time (s)'
    BDD_NODES = 'BDD Nodes'
    CONFIGURATIONS = 'Configurations'


def main(fm_filepath: str) -> dict[str, Any]:
    path = pathlib.Path(fm_filepath)
    filename = path.stem

    csv_entry = {}
    csv_entry[CSVHeader.MODEL.value] = filename

    timer = codetiming.Timer(logger=None)  # A timer to get execution time

    # Read the feature model
    try:
        LOGGER.debug(f'Reading feature model {path}')
        fm = UVLReader(fm_filepath).transform()
    except FlamaException as e:
        LOGGER.error(f'Error reading feature model {path}: {e}')
        return csv_entry
    csv_entry[CSVHeader.FEATURES.value] = len(fm.get_features())
    csv_entry[CSVHeader.CONSTRAINTS.value] = len(fm.get_constraints())

    # Convert the FM to logic
    try:
        LOGGER.debug(f'Converting FM to logic...')
        timer.start()
        elapsed_time = timer.stop()
        var_filepath, exp_filepath, securevars_filepath = fm2logic.fm2logic(fm_filepath, fm)
    except Exception as e:
        LOGGER.error(f'Error converting FM to logic {path}: {e}')
        csv_entry[CSVHeader.UVL2LOGIC_TIME.value] = ERROR_STR
        return csv_entry
    LOGGER.debug(f'Generated logic files: {var_filepath}, {exp_filepath}, {securevars_filepath}')
    # Get number of variables and clauses
    with open(var_filepath, 'r') as file:
        num_variables = len(file.read().split())
    with open(exp_filepath, 'rb') as file:
        num_lines = sum(1 for _ in file)
    csv_entry[CSVHeader.VARIABLES.value] = num_variables
    csv_entry[CSVHeader.CLAUSES.value] = num_lines
    csv_entry[CSVHeader.UVL2LOGIC_TIME.value] = utils.float2exp(elapsed_time, PRECISION)

    # Get initial order of variables
    try:
        LOGGER.debug(f'Getting initial order...')
        timer.start()
        sifting_filepath = logic2bdd.get_initial_order(var_filepath, exp_filepath, TIMEOUT)
        elapsed_time = timer.stop()
    except Exception as e:
        LOGGER.error(f'Error getting initial order for files {var_filepath}, {exp_filepath}: {e}')
        csv_entry[CSVHeader.FASTORDER_TIME.value] = ERROR_STR
        return csv_entry
    if sifting_filepath is None:
        LOGGER.warning(f'Timeout getting initial order for files {var_filepath}, {exp_filepath}')
        csv_entry[CSVHeader.FASTORDER_TIME.value] = TIMEOUT_STR
        return csv_entry
    LOGGER.debug(f'Generated order file: {sifting_filepath}')
    csv_entry[CSVHeader.FASTORDER_TIME.value] = utils.float2exp(elapsed_time, PRECISION)

    # Build the BDD
    try:
        LOGGER.debug(f'Building BDD...')
        timer.start()
        bdd_filepath = logic2bdd.build_bdd(var_filepath, exp_filepath, sifting_filepath, TIMEOUT)
        elapsed_time = timer.stop()
    except Exception as e:
        LOGGER.error(f'Error building the BDD for files {var_filepath}, {exp_filepath}, {sifting_filepath}: {e}')
        csv_entry[CSVHeader.LOGIC2BDD_TIME.value] = ERROR_STR
        return csv_entry
    if bdd_filepath is None:
        LOGGER.warning(f'Timeout building the BDD for files {var_filepath}, {exp_filepath}')
        csv_entry[CSVHeader.LOGIC2BDD_TIME.value] = TIMEOUT_STR
        return csv_entry
    LOGGER.debug(f'Generated BDD file: {bdd_filepath}')
    csv_entry[CSVHeader.LOGIC2BDD_TIME.value] = utils.float2exp(elapsed_time, PRECISION)
    # Analyze the BDD
    with open(bdd_filepath, 'r') as file:
        nnodes_line = [line for line in file.readlines() if line.startswith('.nnodes')][0]
        num_nodes = int(nnodes_line.split()[1].strip())
    csv_entry[CSVHeader.BDD_NODES.value] = num_nodes
    nof_configs = utils.count_configurations(bdd_filepath)
    csv_entry[CSVHeader.CONFIGURATIONS.value] = utils.int2sci(nof_configs) if nof_configs > 1e6 else nof_configs

    return csv_entry


def main_dir(dirpath: str) -> None:
    csv_writer = CSVWriter(CSV_FILE_RESULTS, [h.value for h in CSVHeader])
    with open(CSV_FILE_RESULTS, 'r') as results_file:
        content = results_file.read()
    total_models = 0
    models_filepaths = utils.get_filepaths(dirpath, ['uvl'])
    n_models = len(models_filepaths)
    LOGGER.info(f'#Models to be processed: {n_models}')
    for i, uvl_filepath in enumerate(models_filepaths, 1):
        path = pathlib.Path(uvl_filepath)
        filename = path.stem
        if filename in content:
            LOGGER.info(f'Skipped model {uvl_filepath} ({i}/{n_models}, {round(i/n_models*100,2)}%).')    
        else:
            LOGGER.debug(f'Processing model {uvl_filepath} ({i}/{n_models}, {round(i/n_models*100,2)}%).')
            total_models += 1
            csv_entry = main(uvl_filepath)
            csv_writer.write_row(csv_entry)
    LOGGER.info(f'#Models processed: {total_models}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UVL2BDD: Create a BDD from a UVL feature model.')
    parser.add_argument(metavar='path', dest='path', type=str, help='Input feature model (.uvl) or directory with models.')
    args = parser.parse_args()

    if os.path.isdir(args.path):
        main_dir(args.path)
    else:
        csv_writer = CSVWriter(CSV_FILE_RESULTS, [h.value for h in CSVHeader])
        csv_entry = main(args.path)
        csv_writer.write_row(csv_entry)
        
