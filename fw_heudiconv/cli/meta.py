import os
import sys
import argparse
import warnings
import flywheel
import logging
import re
import pandas as pd
import shutil
from pathlib import Path
from fw_heudiconv.backend_funcs.convert import get_nested

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


def attach_to_object(object, file, dry_run):

    if dry_run:
        logger.info("{}\t-->\t{}".format(file.ljust(20), object.label))
        return 0
    my_file = Path(file)
    if my_file.is_file():
        object.upload_file(my_file)
        return 0
    else:
        logger.error("Couldn't access file {}".format(file))
        return 1


def autogen_participants_meta(project_obj, sessions, dry_run):

    participants = []
    for sess in sessions:

        participants.append({
            'participant_id': get_BIDS_label_from_session(sess),
            'flywheel_id': sess.subject.label
        })
    df = pd.DataFrame(participants)
    df = df[['participant_id', 'flywheel_id']]

    tmpdir = "./tmp"
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
        df.to_csv(tmpdir+"/participants.tsv", index=False, sep="\t", na_rep="n/a")
        result = attach_to_object(project_obj, tmpdir+"/participants.tsv", dry_run)
        shutil.rmtree(tmpdir)
        return result
    else:
        logger.error("Couldn't create temp space to create .tsv files")
        return 1


def autogen_sessions_meta(client, sessions, dry_run):

    results = []
    subjects = {}
    for sess in sessions:
        sub = sess.subject.label
        if sub in subjects:
            subjects[sub].append(sess)
        else:
            subjects[sub] = [sess]

    tmpdir = "./tmp"

    for k, v in subjects.items():

        subject_label = get_BIDS_label_from_session(v[0], 'sub')
        if subject_label is None:
            logger.error("Subject {} has no BIDS session data".format(k))
            continue
        else:
            sessions_dict = {
                'session_id': [get_BIDS_label_from_session(sess, 'ses') for sess in v],
                'flywheel_id': [sess.label for sess in v]
            }

            df = pd.DataFrame(sessions_dict)

            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)
                df.to_csv(tmpdir+"/sub-{}_sessions.tsv".format(subject_label), index=False, sep="\t", na_rep="n/a")
                subject_object = client.get(v[0].subject.id)
                results.append(attach_to_object(subject_object, tmpdir+"/sub-{}_sessions.tsv".format(subject_label), dry_run))
                shutil.rmtree(tmpdir)
            else:
                logger.error("Couldn't create temp space to create .tsv files")

    if any([x == 1 for x in results]):
        return 1
    else:
        return 0


def upload_to_session(client, sessions, label, infile, dry_run):

    subjects = {}
    for sess in sessions:
        sub = sess.subject.label
        if sub in subjects:
            subjects[sub].append(sess)
        else:
            subjects[sub] = [sess]

    tmpdir = "./tmp"

    if label in subjects:
        target_sess = subjects[label][0]
        subject_object = client.get(target_sess.subject.id)
        result = attach_to_object(subject_object, infile, dry_run)
        return result
    else:
        logger.error("Given subject label {} not found!".format(label))
        return 1


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
    sessions_meta.add_argument(
        "--upload-sessions-meta",
        help="<SUBJECT_LABEL> <PATH_TO_FILE> for *_sessions.tsv metadata file to upload",
        nargs=2,
        action='append'
    )

    # scans file
    parser.add_argument(
        "--scans",
        help="Path to a scans.tsv metadata file to upload",
        action='store'
    )

    # dataset descr file
    parser.add_argument(
        "--dataset-description",
        help="Path to a dataset_description.json metadata file to upload",
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
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )

    return parser


def main():

    logger.info("{:=^70}\n".format(": fw-heudiconv metadata manager starting up :"))
    status = [0]

    parser = get_parser()
    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if args.api_key:
            fw = flywheel.Client(args.api_key)
        else:
            fw = flywheel.Client()
    assert fw, "Your Flywheel CLI credentials aren't set!"

    # Print a lot if requested
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.dry_run:
        logger.info("Running in `dry-run` mode (no changes will be applied).")

    sessions = initialise_dataset(fw, args.project, args.subject, args.session, args.dry_run)

    if len(sessions) < 1:
        status = 1
        logger.error("No sessions found!")
        sys.exit(status)

    project_level_uploads = {
        'README': args.readme,
        'CHANGES': args.changes,
        'CODE': args.code,
        'dataset_description.json': args.dataset_description
    }

    project_obj = fw.get(sessions[0].project)

    for k,v in project_level_uploads.items():

        if v is not None:
            logger.info("Attempting to attach {} to project".format(v))
            status.append(attach_to_object(project_obj, v, args.dry_run))

    if args.autogen_participants_meta:

        logger.info("Auto-generating participants.tsv...")
        status.append(autogen_participants_meta(project_obj, sessions, args.dry_run))

    elif args.upload_participants_meta:

        logger.info("Attempting to attach {} to project...".format(args.upload_participants_meta))
        status.append(attach_to_object(project_obj, args.upload_participants_meta, args.dry_run))

    if args.autogen_sessions_meta:

        logger.info("Auto-generating *_sessions.tsv...")
        status.append(autogen_sessions_meta(fw, sessions, args.dry_run))

    elif args.upload_sessions_meta:
        for tup in args.upload_sessions_meta:
            logger.info("Attempting to attach {} to {}...".format(tup[1], tup[0]))
            status.append(upload_to_session(fw, sessions, tup[0], tup[1], args.dry_run))

    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv metadata manager :"))
    if any([x == 1 for x in status]):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
