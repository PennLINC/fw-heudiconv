import flywheel
import warnings
import os
import sys
import shutil
import subprocess as sub
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-validator')


def validate_local(path, verbose):

    command = ['bids-validator', path]
    if verbose:
        command.extend(['--verbose'])
    p = sub.Popen(command, stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
    output, error = p.communicate()

    logger.info(output)
    if p.returncode != 0:
        logger.info(error)
    return p.returncode


def fw_heudiconv_export(proj, subjects=None, sessions=None, destination="tmp", name="bids_directory"):

    command = ['fw-heudiconv-export', '--project', ' '.join(proj), '--destination', destination, '--directory_name', name]

    if subjects:
        command.extend(['--subject'] + subjects)
    if sessions:
        command.extend(['--session'] + sessions)

    p = sub.Popen(command, stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
    output, error = p.communicate()

    logger.info(output)
    if p.returncode != 0:
        logger.info(error)
    return p.returncode


def get_parser():

    parser = argparse.ArgumentParser(
        description="Validate BIDS-curated data on Flywheel. A simple wrapper around the original BIDS Validator https://github.com/bids-standard/bids-validator")

    location = parser.add_mutually_exclusive_group(required=True)
    location.add_argument(
        '--local',
        help="Validate a local directory of BIDS data",
        action='store_true')
    location.add_argument(
        '--flywheel',
        help="Validate a BIDS project on Flywheel",
        action='store_true')

    parser.add_argument(
        "--directory",
        help="Path to existing BIDS data directory OR temp space used for validation",
        default="bids_directory",
        required=False,
        type=str
    )
    parser.add_argument(
        "--project",
        help="The project on Flywheel",
        nargs="+"
    )
    parser.add_argument(
        "--subject",
        help="The subject(s) on Flywheel to validate",
        nargs="+",
        default=None,
        type=str
    )
    parser.add_argument(
        "--session",
        help="The session(s) on Flywheel to validate",
        nargs="+",
        default=None,
        type=str
    )
    parser.add_argument(
        "--verbose",
        help="Pass on <VERBOSE> flag to bids-validator",
        default=False,
        action='store_true'
    )

    return parser



def main():

    parser = get_parser()

    args = parser.parse_args()

    exit = 1

    if args.local:
        if not os.path.exists(args.directory):
            logger.error("Couldn't find the BIDS dataset!")
            sys.exit(exit)
        else:
            logger.info("Validating local BIDS dataset {}".format(args.directory))
            exit = validate_local(args.directory, args.verbose)

    else:
        if not os.path.exists(args.directory):
            logger.info("Creating download directory...")
            os.makedirs(args.directory)

        if not args.project:
            logger.error("No project on Flywheel specified!")
            sys.exit(exit)

        success = fw_heudiconv_export(proj=args.project, subjects=args.subject, sessions=args.session, destination=args.directory, name='bids_directory')

        if success == 0:
            path = Path(args.directory + '/bids_directory')
            validate_local(path, args.verbose)
            shutil.rmtree(path)

    sys.exit(exit)

if __name__ == "__main__":
    main()
