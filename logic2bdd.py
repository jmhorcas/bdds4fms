import os
import argparse
import pathlib
import logging
import subprocess

from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from utils.fm_secure_features_names import FMSecureFeaturesNames
from utils.pl_writer import PLWriter
from utils.utils import get_filepaths


MIN_NODES = 200000
CONSTRAINT_REORDER = 'minspan'
TIMEOUT = 7200  # in seconds, 2 hours


def get_initial_order(varfile: str, expfile: str) -> str:
    """Given the variables and expressions files, return the initial order of the variables in a 
    <<file>>-sifting.var file."""
    path = pathlib.Path(varfile)
    filename = path.stem
    dir = path.parent
    outputfile = str(dir / f'{filename}-sifting.var')

    command = ['fastOrder', '-nosubexp', '-sifting', varfile, expfile, outputfile]  # These options are fine for models without numerical constraints
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    #process.wait()
    stdout, stderr = process.communicate()
    print(f'OUT: {stdout}')
    print(f'ERR: {stderr}')
    return outputfile


def build_bdd(varfile: str, expfile: str, orderfile: str, timeout: int = TIMEOUT) -> str:
    """Build the BDD using the given variables, expressions and order files."""
    path = pathlib.Path(varfile)
    filename = path.stem
    dir = path.parent
    outputfile = str(dir / f'{filename}.dddmp')

    command = [timeout, TIMEOUT, 'Logic2BDD', '-out', outputfile, '-constraint-reorder', CONSTRAINT_REORDER, '-min-nodes', MIN_NODES, '-score', orderfile, varfile, expfile]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    #process.wait()
    stdout, stderr = process.communicate()
    print(f'OUT: {stdout}')
    print(f'ERR: {stderr}')
    return outputfile


def reduce_size() -> None:
    """Reduce the size of the BDD."""
    pass


def build_models(dirpath: str) -> None:
    total_models = 0
    models_with_errors = []
    models_with_missing_files = []
    for varfile in get_filepaths(dirpath, ['var']):
        path = pathlib.Path(varfile)
        filename = path.stem
        dir = path.parent
        expfile = str(dir / f'{filename}.exp')
        if not os.path.isfile(expfile):
            print(f'Expression file not found for {filename}. Skipped.')
            models_with_missing_files.append(varfile)
        else:
            try:
                build_model(varfile, expfile)
                total_models += 1
            except FlamaException:
                print('... error.')
                models_with_errors.append(varfile)

    print(f'{total_models} total models.')
    print(f'{len(models_with_errors)} models with errors:')
    for i, filepath in enumerate(models_with_errors, 1):
        print(f'|-{i}: {filepath}')
    print(f'{len(models_with_missing_files)} models with missing files:')
    for i, filepath in enumerate(models_with_missing_files, 1):
        print(f'|-{i}: {filepath}')


def build_model(varfile: str, expfile: str) -> None:
    orderfile = get_initial_order(varfile, expfile)
    bddfile = build_bdd(varfile, expfile, orderfile)
    print('BDD file: {bddfile}')


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