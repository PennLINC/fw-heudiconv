import argparse
import warnings
import logging
import flywheel
import os
import pprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-reproin')


def check(string):
    
    assert isinstance(string, str), "Input is not a string!"
    
    result = re.search(r'^((anat)|(func)|(fmap)|(dwi))-[a-zA-Z0-9]+(_ses-[a-zA-Z0-9]+)?(_task-[a-zA-Z0-9]+)?(_acq-[a-zA-Z0-9]+)?(_ce-[a-zA-Z0-9]+)?(_dir-[a-zA-Z0-9]+)?(_rec-[a-zA-Z0-9]+)?(_run-[a-zA-Z0-9]+)?', string)
    
    if result:
        return True
    else:
        return False


def get_parser():

    parser = argparse.ArgumentParser(
        description="Inspect reproin naming protocols")

    parser.add_argument(
        "--input-path",
        help="Path to a text file containing reproin names",
        required=True,
        type=str
    )
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )
    return parser


def main():

    logger.info("{:=^70}\n".format(": fw-heudiconv reproin checker starting up :"))
    parser = get_parser()
    args = parser.parse_args()

    try:
        if os.path.isfile(args.input_path):
            with open(args.input_path) as f:
                names = f.read().splitlines()

        else:
            raise FileNotFoundError
    except FileNotFoundError as e:
        logger.error("Couldn't load the input data file!")
        logger.error(e)
        sys.exit(1)

    check_results = {}

    for name in names:

        check_results[name] = check(name)

    if all(list(check_results.values())):

        logger.info("All names pass UPenn reproin specification!")

    else:

        fails = [key for (key,value) in check_results.items() if value is False]

        logger.info("The following names fail UPenn reproin specification:\n\t" + "\n\t".join(fails))

    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv reproin checker :"))
