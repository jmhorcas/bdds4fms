import os
import re
import argparse
import pathlib
import logging
import subprocess

from utils.utils import get_filepaths


class BDDException(Exception):
    pass


MIN_NODES = 200000
CONSTRAINT_REORDER = 'minspan'
TIMEOUT = 7200  # in seconds, 2 hours

# Executables
FASTORDER = '../bdds/bin/fastOrder'
LOGIC2BDD = '../bdds/bin/Logic2BDD'


def get_initial_order(varfile: str, expfile: str) -> str:
    """Given the variables and expressions files, return the initial order of the variables in a 
    <<file>>-sifting.var file."""
    path = pathlib.Path(varfile)
    filename = path.stem
    dir = path.parent
    outputfile = str(dir / f'{filename}-sifting.var')

    command = [FASTORDER, '-nosubexp', '-sifting', varfile, expfile, outputfile]  # These options are fine for models without numerical constraints
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
    outputfile = str(dir / f'{filename}.dddmp')

    command = ['timeout', str(timeout), LOGIC2BDD, '-out', outputfile, '-constraint-reorder', CONSTRAINT_REORDER, '-min-nodes', str(MIN_NODES), '-score', orderfile, varfile, expfile]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    s = stdout.strip().splitlines()[-1]
    match = re.search(r'\d+ ms', s)
    time = match.group(0) if match else None
    print(f'|- Time: {time}')
    #print(f'OUT: {stdout}')
    #print(f'ERR: {stderr}')
    return outputfile


def reduce_size() -> None:
    """Reduce the size of the BDD."""
    pass


def build_models(dirpath: str) -> None:
    total_models = 0
    models_with_errors = 0
    models_with_missing_files = 0
    for i, varfile in enumerate(get_filepaths(dirpath, ['var']), 1):
        print(f'{i}: {varfile}...')
        path = pathlib.Path(varfile)
        filename = path.stem
        dir = path.parent
        expfile = str(dir / f'{filename}.exp')
        if not os.path.isfile(expfile):
            print(f'|- Expression file not found for {filename}. Skipped.')
            models_with_missing_files += 1
        else:
            try:
                build_model(varfile, expfile)
                total_models += 1
            except (BDDException, Exception) as e:
                models_with_errors += 1
                print(f'|- bdd for {varfile} could not been generated: {e}.')

    print(f'{total_models} total models.')
    print(f'{models_with_errors} models with errors:')
    print(f'{models_with_missing_files} models with missing files:')


def build_model(varfile: str, expfile: str) -> None:
    orderfile = get_initial_order(varfile, expfile)
    if not pathlib.Path(orderfile).exists():
        raise BDDException(f'Initial order could not been generated.')
    bddfile = build_bdd(varfile, expfile, orderfile)
    if not pathlib.Path(bddfile).exists():
        raise BDDException(f'BDD could not been generated (possible timeout).')


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    
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