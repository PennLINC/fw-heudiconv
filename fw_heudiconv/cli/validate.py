import os
import sys
import shutil
import logging
import argparse
import warnings
import re
from pathlib import Path
import subprocess as sub
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-validator')


def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)


def find_all(regex, text):

    match_list = []
    while True:
        match  = re.search(regex, text)
        if match:
            match_list.append(match.group(0))
            text = text[match.end():]
        else:
            return match_list


def validate_local(path, verbose, tabulate='.'):

    logger.info("Launching bids-validator...")
    command = ['bids-validator', path]
    if verbose:
        command.extend(['--verbose'])
    p = sub.Popen(command, stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
    output, error = p.communicate()

    logger.info(output)

    if p.returncode != 0:
        logger.info(error)

    clean_output = re.sub('\s+',' ', escape_ansi(output))
    issues = find_all(r'\[[A-Z]+\].+?(?=(\[[A-Z]+\]|Summary))', clean_output)

    if issues and os.path.exists(tabulate):

        logger.info("Parsing issues and writing to issues.csv")
        issues_tuples = []

        for iss in issues:
            issue_type_match = re.search(r'\[[A-Z]+\]', iss)
            issue_type = iss[:issue_type_match.end()]
            issue_description = iss[issue_type_match.end():].lstrip()
            issue_evidence = find_all(
                r'(?<=Evidence: ).+?(?=(Evidence|\[[A-Z]+\]))', issue_description
                )
            if issue_evidence:
                evidence_ix = re.search('Evidence', issue_description).start()
                issue_description = issue_description[:evidence_ix]
            else:
                issue_evidence = ''

            issues_tuples.append((issue_type, issue_description, issue_evidence))

        issues_df = pd.DataFrame(issues_tuples, columns=['Type', 'Description', 'Evidence'])
        issues_df_full = issues_df.explode('Evidence')
        logger.info("Writing...")
        issues_df_full.to_csv(tabulate + '/issues.csv', index=False)

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
        default=".",
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
        "--tabulate",
        default=".",
        required=False,
        type=str,
        help="Directory to save tabulation of errors"
    )
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )
    parser.add_argument(
        "--dry-run",
        help=argparse.SUPPRESS,
        action='store_false',
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

        #if not os.path.exists(args.directory):
        #    logger.info("Creating download directory...")
        #    os.makedirs(args.directory)

        success = fw_heudiconv_export(proj=args.project, subjects=args.subject, sessions=args.session, destination=args.directory, name='bids_directory', key=args.api_key)

        if success == 0:
            path = Path(args.directory, 'bids_directory')
            exit = validate_local(path, args.verbose, args.tabulate)
            shutil.rmtree(path)

        else:

            logger.error("There was a problem downloading the data to a temp space for validation!")
    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv validator :"))
    sys.exit(exit)

if __name__ == "__main__":
    main()
