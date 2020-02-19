import argparse
import warnings
import logging
import flywheel
import os
import pprint
import re
import sys
from fw_heudiconv.example_heuristics.reproin_Upenn import parse_protocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-reproin')


def check(string, verbose):
    '''
    https://regex101.com/r/w0SRcs/1/
    '''
    assert isinstance(string, str), "Input is not a string!"

    result = re.search(
        r'^([A-Z]+:)?'
        '((anat)|(func)|(fmap)|(dwi))-([\w]+){1}'
        '(_ses-[a-zA-Z0-9]+)?'
        '(_task-[a-zA-Z0-9]+)?'
        '(_acq-[a-zA-Z0-9]+)?'
        '(_ce-[a-zA-Z0-9]+)?'
        '(_dir-[a-zA-Z0-9]+)?'
        '(_rec-[a-zA-Z0-9]+)?'
        '(_run-[a-zA-Z0-9]+)?'
        '(__.*)?$',
        string)

    if result:

        if verbose:
            print(string + "\n\t -> " + parse_protocol(string) + "\n")

        return True
    else:
        return False


def get_parser():

    parser = argparse.ArgumentParser(
        description="Inspect reproin naming protocols")

    parser.add_argument(
        "--protocol-names",
        help="Path to a text file containing reproin-compliant protocol names",
        required=True,
        type=str
    )
    parser.add_argument(
        "--api-key",
        help=argparse.SUPPRESS,
        action='store',
        default=None
    )
    parser.add_argument(
        "--project",
        help=argparse.SUPPRESS,
        action='store',
        default=None
    )
    parser.add_argument(
        "--subject",
        help=argparse.SUPPRESS,
        nargs="+",
        default=None
    )
    parser.add_argument(
        "--session",
        help=argparse.SUPPRESS,
        nargs="+",
        default=None
    )
    parser.add_argument(
        "--verbose",
        help="Print ongoing messages of progress",
        action='store_true',
        default=False
    )
    parser.add_argument(
        "--dry-run",
        help=argparse.SUPPRESS,
        action='store_true',
        default=False
    )
    return parser


def main():

    logger.info("{:=^70}\n".format(": fw-heudiconv reproin checker starting up :"))
    parser = get_parser()
    args = parser.parse_args()

    try:
        if os.path.isfile(args.protocol_names):
            with open(args.protocol_names) as f:
                names = f.read().splitlines()

        else:
            raise FileNotFoundError
    except FileNotFoundError as e:
        logger.error("Couldn't load the input data file!")
        logger.error(e)
        sys.exit(1)

    check_results = {}

    for name in names:

        check_results[name] = check(name, args.verbose)

    if all(list(check_results.values())):

        logger.info("All names pass UPenn reproin specification!")

    else:

        fails = [key for (key,value) in check_results.items() if value is False]

        logger.info("The following names fail UPenn reproin specification:\n\t" + "\n\t".join(fails))

    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv reproin checker :"))
