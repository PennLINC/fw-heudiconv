import os
import sys
import shutil
import subprocess as sub
import logging
import argparse
import warnings
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-validator')


def validate_local(path, verbose):

    logger.info("Launching bids-validator...")
    command = ['bids-validator', path]
    if verbose:
        command.extend(['--verbose'])
    p = sub.Popen(command, stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
    output, error = p.communicate()

    logger.info(output)
    if p.returncode != 0:
        logger.info(error)
    return p.returncode


def fw_heudiconv_export(proj, subjects=None, sessions=None, destination="tmp", name="bids_directory", key=None):

    logger.info("Launching fw-heudiconv-export...")
    command = ['fw-heudiconv-export', '--project', ' '.join(proj), '--destination', destination, '--directory-name', name]

    if subjects:
        command.extend(['--subject'] + subjects)
    if sessions:
        command.extend(['--session'] + sessions)
    if key:
        command.extend(['--api-key'] + [key])

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
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )
    return parser



def main():

    logger.info("{:=^70}\n".format(": fw-heudiconv validator starting up :"))

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
        if not args.project:
            logger.error("No project on Flywheel specified!")
            sys.exit(exit)

        if not os.path.exists(args.directory):
            logger.info("Creating download directory...")
            os.makedirs(args.directory)

        success = fw_heudiconv_export(proj=args.project, subjects=args.subject, sessions=args.session, destination=args.directory, name='bids_directory', key=args.api_key)

        if success == 0:
            path = Path(args.directory + '/bids_directory')
            exit = validate_local(path, args.verbose)
            shutil.rmtree(path)

        else:

            logger.error("There was a problem downloading the data to a temp space for validation!")
    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv validator :"))
    sys.exit(exit)

if __name__ == "__main__":
    main()
