import os
import sys
import importlib
import argparse
import warnings
import flywheel
import pprint
import validators
import requests
from collections import defaultdict
from fw_heudiconv.backend_funcs.convert import apply_heuristic, confirm_intentions, confirm_bids_namespace, verify_attachment, upload_attachment
from fw_heudiconv.backend_funcs.query import get_seq_info
from heudiconv import utils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-curator')


def pretty_string_seqinfo(seqinfo):
    tr = seqinfo.TR if seqinfo.TR is not None else -1.0
    te = seqinfo.TE if seqinfo.TE is not None else -1.0
    rep = '{protocol_name}: \n\t\t[TR={tr:} TE={te} ' \
          'shape=({dim1}, {dim2}, {dim3}, {dim4}) ' \
          'image_type={image_type}] ({idnum})\n'
    try:
        rep_fmt = rep.format(protocol_name=seqinfo.protocol_name, tr=tr,
                             te=te, dim1=seqinfo.dim1, dim2=seqinfo.dim2,
                             dim3=seqinfo.dim3, dim4=seqinfo.dim4,
                             image_type=seqinfo.image_type,
                             idnum=seqinfo.series_id)
    except Exception as e:
        logger.warning("Unparseable field in %s.\n\n Got error: %s", seqinfo, e)
        rep_fmt = 'ERROR'
    return rep_fmt


def convert_to_bids(client, project_label, heuristic_path, subject_labels=None,
                    session_labels=None, dry_run=False):
    """Converts a project to bids by reading the file entries from flywheel
    and using the heuristics to write back to the BIDS namespace of the flywheel
    containers

    Args:
        client (Client): The flywheel sdk client
        project_label (str): The label of the project
        heuristic_path (str): The path to the heuristic file or the name of a
            known heuristic
        subject_code (str): The subject code
        session_label (str): The session label
        dry_run (bool): Print the changes, don't apply them on flywheel
    """

    # Make sure we can find the heuristic
    logger.info("Loading heuristic file...")
    try:

        if os.path.isfile(heuristic_path):
            heuristic = utils.load_heuristic(heuristic_path)

        elif "github" in heuristic_path and validators.url(heuristic_path):

            # read from github
            try:
                response = requests.get(heuristic_path)

                if response.ok:

                    name = 'heuristic'
                    spec = importlib.util.spec_from_loader(name, loader=None)

                    heuristic = importlib.util.module_from_spec(spec)

                    code = response.text

                    exec(code, heuristic.__dict__)

                else:

                    logger.error("Couldn't find a valid URL for this heuristic at:\n\n" + heuristic_path + "\n")
                    raise ModuleNotFoundError

            except:
                logger.error("Trouble retrieving the URL!")
                raise ModuleNotFoundError("Is this a valid URL to a heuristic on Github? Please check spelling!")

        else:
            heuristic = importlib.import_module('fw_heudiconv.example_heuristics.{}'.format(heuristic_path))

    except ModuleNotFoundError as e:
        logger.error("Couldn't load the specified heuristic file!")
        logger.error(e)
        sys.exit(1)

    logger.info("Heuristic loaded successfully!")

    if dry_run:
        logger.setLevel(logging.DEBUG)

    logger.info("Querying Flywheel server...")
    project_obj = client.projects.find_first('label="{}"'.format(project_label))
    assert project_obj, "Project not found! Maybe check spelling...?"
    logger.debug('Found project: %s (%s)', project_obj['label'], project_obj.id)
    project_obj = confirm_bids_namespace(project_obj, dry_run)

    sessions = client.get_project_sessions(project_obj.id)
    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label'] in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]

    assert sessions, "No sessions found!"
    logger.debug('Found sessions:\n\t%s',
                 "\n\t".join(['%s (%s)' % (ses['label'], ses.id) for ses in sessions]))

    # try subject/session label functions
    if hasattr(heuristic, "ReplaceSubject"):
        subject_rename = heuristic.ReplaceSubject
    else:
        subject_rename = None
    if hasattr(heuristic, "ReplaceSession"):
        session_rename = heuristic.ReplaceSession
    else:
        session_rename = None

    # try attachments
    if hasattr(heuristic, "AttachToProject"):
        logger.info("Processing project attachments based on heuristic file")

        attachments = heuristic.AttachToProject()

        if not isinstance(attachments, list):
            attachments = [attachments]

        for at in attachments:

            upload_attachment(
                client, project_obj, level='project', attachment_dict=at,
                subject_rename=subject_rename, session_rename=session_rename,
                folders=['anat', 'dwi', 'func', 'fmap', 'perf'],
                dry_run=dry_run
                    )

    '''if hasattr(heuristic, "AttachToSubject"):

        logger.info("Processing subject attachments based on heuristic file")

        attachments = heuristic.AttachToSubject()

        if not isinstance(attachments, list):
            attachments = [attachments]

        for at in attachments:

            logger.debug(
            "\tFilename: {}\n\tData: {}\n\tMIMEType: {}".format(
                at['name'], at['data'], at['type']
                )
            )

            verify_name, verify_data, verify_type = verify_attachment(at['name'], at['data'], at['type'])

            if not all([verify_name, verify_data, verify_type]):

                logger.warning("Attachments may not be valid for upload!")
                logger.debug(
                "\tFilename valid: {}\n\tData valid: {}\n\tMIMEType valid: {}".format(
                    verify_name, verify_data, verify_type
                    )
                )

            if not dry_run:
                subjects = [x.subject for x in sessions]
                file_spec = flywheel.FileSpec(at['name'], at['data'], at['type'])
                [sub.upload_file(file_spec) for sub in subjects]'''

    num_sessions = len(sessions)
    for sesnum, session in enumerate(sessions):

        # Find SeqInfos to apply the heuristic to
        logger.info("Applying heuristic to %s (%d/%d)...", session.label, sesnum+1,
                    num_sessions)

        seq_infos = get_seq_info(client, project_label, [session])
        logger.debug(
            "Found SeqInfos:\n%s",
            "\n\t".join([pretty_string_seqinfo(seq) for seq in seq_infos]))

        # apply heuristic to seqinfos
        to_rename = heuristic.infotodict(seq_infos)

        if not to_rename:
            logger.debug("No changes to apply!")
            continue

        # try intendedfors
        intention_map = defaultdict(list)
        if hasattr(heuristic, "IntendedFor"):
            logger.info("Processing IntendedFor fields based on heuristic file")
            intention_map.update(heuristic.IntendedFor)
            logger.debug("Intention map: %s",
                         pprint.pformat(
                             [(k[0], v) for k, v in dict(intention_map).items()]))

        # try metadataextras
        metadata_extras = defaultdict(list)
        if hasattr(heuristic, "MetadataExtras"):
            logger.info("Processing Medatata fields based on heuristic file")
            metadata_extras.update(heuristic.MetadataExtras)
            logger.debug("Metadata extras: %s", metadata_extras)

        # try subject/session label functions
        if hasattr(heuristic, "ReplaceSubject"):
            subject_rename = heuristic.ReplaceSubject
        else:
            subject_rename = None
        if hasattr(heuristic, "ReplaceSession"):
            session_rename = heuristic.ReplaceSession
        else:
            session_rename = None

        # try attachments
        if hasattr(heuristic, "AttachToSession"):
            logger.info("Processing session attachments based on heuristic file")

            attachments = heuristic.AttachToSession()

            if not isinstance(attachments, list):
                attachments = [attachments]

            for at in attachments:

                upload_attachment(
                    client, session, level='session', attachment_dict=at,
                    subject_rename=subject_rename, session_rename=session_rename,
                    folders=['anat', 'dwi', 'func', 'fmap', 'perf'],
                    dry_run=dry_run
                        )

        # final prep
        if not dry_run:
            logger.info("Applying changes to files...")

        for key, val in to_rename.items():

            # assert val is list
            if not isinstance(val, set):
                val = set(val)
            for seqitem, value in enumerate(val):
                apply_heuristic(client, key, value, dry_run, intention_map[key],
                                metadata_extras[key], subject_rename, session_rename,
                                seqitem+1)

        confirm_intentions(client, session, dry_run)
        print("\n")


def get_parser():

    parser = argparse.ArgumentParser(
        description="Use a heudiconv heuristic to curate data into BIDS on flywheel")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        required=True
    )
    parser.add_argument(
        "--heuristic",
        help="Path to a heudiconv-style heuristic file",
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
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )

    return parser


def main():

    logger.info("{:=^70}\n".format(": fw-heudiconv curator starting up :"))

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

    convert_to_bids(client=fw,
                    project_label=args.project,
                    heuristic_path=args.heuristic,
                    session_labels=args.session,
                    subject_labels=args.subject,
                    dry_run=args.dry_run)

    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv curator :"))
    sys.exit()


if __name__ == '__main__':
    main()
