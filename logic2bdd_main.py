import os
import re
import argparse
import pathlib
import logging
import subprocess

from utils.utils import get_filepaths


logging.basicConfig(filename='logic2bdd.log', encoding='utf-8', level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)    


class BDDException(Exception):
    pass


MIN_NODES = 200000
CONSTRAINT_REORDER = 'minspan'
TIMEOUT = 7200  # in seconds, 2 hours

# Executables
FASTORDER = '../bdds/bin/fastOrder'
LOGIC2BDD = '../bdds/bin/Logic2BDD'


def get_initial_order(varfile: str, expfile: str, timeout: int = TIMEOUT) -> str:
    """Given the variables and expressions files, return the initial order of the variables in a 
    <<file>>-sifting.var file."""
    path = pathlib.Path(varfile)
    filename = path.stem
    dir = path.parent
    outputfile = str(dir / f'{filename}-sifting.var')

    command = ['timeout', str(timeout), FASTORDER, '-nosubexp', '-sifting', varfile, expfile, outputfile]  # These options are fine for models without numerical constraints
    logging.debug(f'Executing command: {command}')
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.wait()
    #stdout, stderr = process.communicate()
    #print(f'OUT: {stdout}')
    #print(f'ERR: {stderr}')
    return outputfile


def build_bdd(varfile: str, expfile: str, orderfile: str, timeout: int = TIMEOUT) -> str:
    """Build the BDD using the given variables, expressions and order files."""
    path = pathlib.Path(varfile)
    filename = path.stem
    dir = path.parent
    outputfile = str(dir.parent / f'bdd/{filename}.dddmp')

    command = ['timeout', str(timeout), LOGIC2BDD, '-out', outputfile, '-constraint-reorder', CONSTRAINT_REORDER, '-min-nodes', str(MIN_NODES), '-score', orderfile, varfile, expfile]
    logging.debug(f'Executing command: {command}')
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    s = stdout.strip().splitlines()[-1]
    if 'Time' not in s:
        logging.warning(f'Timeout for files {varfile}, {expfile}, {orderfile}.')
        raise BDDException('Timeout.')
    logging.warning(f'Time output {s}.')
    match = re.search(r'\d+ ms', s)
    time = match.group(0) if match else None
    logging.warning(f'Time in generating the BDD: {time}.')
    return outputfile


def reduce_size() -> None:
    """Reduce the size of the BDD."""
    pass


def build_models(dirpath: str) -> None:
    total_models = 0
    models_with_errors = 0
    models_with_missing_files = 0
    models_filepaths = get_filepaths(dirpath, ['var'])
    n_models = len(models_filepaths)
    LOGGER.info(f'#Models to be processed: {n_models}')
    for i, varfile in enumerate(models_filepaths, 1):
        LOGGER.debug(f'Processing model {varfile} ({i}/{n_models}, {round(i/n_models*100,2)}%).')
        total_models += 1
        path = pathlib.Path(varfile)
        filename = path.stem
        dir = path.parent
        expfile = str(dir / f'{filename}.exp')
        if not os.path.isfile(expfile):
            LOGGER.warning(f'Expression file not found for {filename}. Skipped.')
            models_with_missing_files += 1
        else:
            try:
                build_model(varfile, expfile)
            except (BDDException, Exception) as e:
                models_with_errors += 1
                LOGGER.error(f'BDD for {varfile} could not been generated. The following error was raised: {e}.')

    LOGGER.info(f'#Models processed: {total_models}.')
    LOGGER.info(f'#Models with errors: {models_with_errors}.')
    LOGGER.info(f'#Models with missing files: {models_with_missing_files}')


def build_model(varfile: str, expfile: str) -> None:
    LOGGER.debug(f'Getting initial order for files: {varfile}, {expfile}.')
    orderfile = get_initial_order(varfile, expfile)
    if not pathlib.Path(orderfile).exists():
        LOGGER.error(f'Initial order could not been generated for {varfile}, {expfile}.')
        raise BDDException(f'Initial order could not been generated.')
    LOGGER.debug(f'Initial order generated: {orderfile}.')
    LOGGER.debug(f'Building BDD for files: {varfile}, {expfile}, {orderfile}.')
    bddfile = build_bdd(varfile, expfile, orderfile)
    if not pathlib.Path(bddfile).exists():
        LOGGER.error(f'BDD could not been generated for {varfile}, {expfile}, {orderfile}.')
        raise BDDException(f'BDD could not been generated.')
    LOGGER.debug(f'BDD generated: {bddfile}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Logic2BDD: Create the BDD using the Logic2BDD tool.')
    parser_model = parser.add_argument_group('Model', 'Model files.')
    parser.add_argument('-var', metavar='varfile', dest='varfile', type=str, required=False, help='Input variable file (.var) of the model.')
    parser.add_argument('-exp', metavar='expfile', dest='expfile', type=str, required=False, help='Input expression file (.exp) of the model.')
    parser.add_argument('-dir', metavar='dirpath', dest='dirpath', type=str, required=False, help='Input directory path with the .var and .exp files of the models.')
    args = parser.parse_args()

    if args.dirpath:
        build_models(args.dirpath)
    elif args.varfile and args.expfile:
        build_model(args.varfile, args.expfile)
    else:
        raise Exception('Invalid arguments.')