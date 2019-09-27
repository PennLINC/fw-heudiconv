import os
import sys
import importlib
import argparse
import warnings
import flywheel
import pprint
import logging
import re
from ..convert import get_nested

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-curator')


def get_BIDS_label_from_session(ses_object, regex='sub'):

    logger.debug("Processing session {}...".format(ses_object.label))
    acquisitions = ses_object.acquisitions()
    pattern = re.compile(r"(?<={}-)[a-zA-z0-9]+(?=_)".format(regex))

    bids_labels = []
    for x in acquisitions:
        files = [f for f in x.files if "nifti" in f.type]
        for y in files:
            bids_labels.append(get_nested(y.to_dict(), 'info', 'BIDS', 'Filename'))
    if bids_labels:
        for b in range(len(bids_labels)):
            if bids_labels[b] is not None:
                label = pattern.search(bids_labels[b])
                if label:
                    bids_labels[b] = label.group()
                else:
                    bids_labels[b] = None

    final_label = set(filter(None, bids_labels))
    if len(final_label) == 1:
        return final_label.pop()
    else:
        return None



def initialise_dataset(client, project_label, subject_labels=None, session_labels=None, dry_run=True):

    if dry_run:
        logger.setLevel(logging.DEBUG)
    logger.info("Querying Flywheel server...")
    project_obj = client.projects.find_first('label="{}"'.format(project_label))
    assert project_obj, "Project not found! Maybe check spelling...?"
    logger.debug('Found project: %s (%s)', project_obj['label'], project_obj.id)
    sessions = client.get_project_sessions(project_obj.id)
    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label'] in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]

    return sessions


def get_parser():

    parser = argparse.ArgumentParser(
        description="Curate BIDS metadata on Flywheel\n\nSee the BIDS spec for details: https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        required=True
    )
    parser.add_argument(
        "--subject",
        help="The subject label(s)",
        nargs="+",
        default=None
    )
    parser.add_argument(
        "--session",
        help="The session label(s)",
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
        help="Don't apply changes",
        action='store_true',
        default=False
    )

    # participants metadata
    participants_meta = parser.add_mutually_exclusive_group()
    participants_meta.add_argument(
        "--autogen-participants-meta",
        help="Automatically generate participants.tsv metadata",
        action='store_true',
        default=False
    )
    participants_meta.add_argument(
        "--upload-participants-meta",
        help="Path to a participants.tsv metadata file to upload",
        action='store'
    )

    # sessions metadata
    sessions_meta = parser.add_mutually_exclusive_group()
    sessions_meta.add_argument(
        "--autogen-sessions-meta",
        help="Automatically generate sub-<label>_sessions.tsv metadata",
        action='store_true',
        default=False
    )
    participants_meta.add_argument(
        "--upload-sessions-meta",
        help="Path to a sessions.tsv metadata file to upload",
        action='store'
    )

    # dataset descr metadata
    dataset_description = parser.add_mutually_exclusive_group()
    dataset_description.add_argument(
        "--autogen-dataset-description",
        help="Automatically generate dataset_description. metadata",
        action='store_true',
        default=False
    )
    dataset_description.add_argument(
        "--upload-dataset-description",
        help="Path to a dataset_description.json metadata file to upload",
        action='store'
    )

    # scans file
    parser.add_argument(
        "--scans",
        help="Path to a scans.tsv metadata file to upload",
        action='store'
    )

    # code files
    parser.add_argument(
        "--code",
        help="Path(s) to additional code files to upload",
        nargs='+',
        action='store'
    )

    # readme file
    parser.add_argument(
        "--readme",
        help="Path to README file to upload",
        action='store'
    )

    # changes file
    parser.add_argument(
        "--changes",
        help="Path to CHANGES file to upload",
        action='store'
    )

    return parser


def main():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fw = flywheel.Client()
    assert fw, "Your Flywheel CLI credentials aren't set!"
    parser = get_parser()
    args = parser.parse_args()

    # Print a lot if requested
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    print(args)


if __name__ == '__main__':
    main()
