import os
import argparse
import logging


from flamapy.metamodels.bdd_metamodel.transformations import DDDMPReader
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDConfigurationsNumber
)


FM_PATH = 'tests/input_fms/featureide_models/pizzas.xml'


def bdd_analysis(bddfile: str):
    bdd_model = DDDMPReader(bddfile).transform()

    nof_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    print(f'#Configurations: {nof_configs}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    
    parser = argparse.ArgumentParser(description='Test BDD: Load a BDD representing a feature model and perform some analysis operation.')
    parser.add_argument(metavar='path', dest='path', type=str, help='Input BDD (.dddmp).')
    args = parser.parse_args()

    bdd_analysis(args.path)
