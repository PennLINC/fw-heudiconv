import os
import sys
import importlib
import argparse
import warnings
import flywheel
from collections import defaultdict
from ..convert import apply_heuristic, confirm_intentions, confirm_bids_namespace
from ..query import get_seq_info
from heudiconv import utils
from heudiconv import heuristics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fwHeuDiConv-curator')

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

    # Find SeqInfos to apply the heuristic to
    seq_infos = get_seq_info(client, project_label, sessions)
    logger.debug(
        "Found SeqInfos:\n%s",
        "\n\t".join([pretty_string_seqinfo(seq) for seq in seq_infos]))

    logger.info("Loading heuristic file...")
    try:
        if os.path.isfile(heuristic_path):
            heuristic = utils.load_heuristic(heuristic_path)
        else:
            heuristic = importlib.import_module('heudiconv.heuristics.{}'.format(heuristic_path))
    except ModuleNotFoundError as e:
        logger.error("Couldn't load the specified heuristic file!")
        logger.error(e)
        sys.exit(1)

    logger.info("Applying heuristic to query results...")
    to_rename = heuristic.infotodict(seq_infos)

    if not to_rename:
        logger.debug("No changes to apply!")
        sys.exit(1)

    intention_map = defaultdict(list)
    if hasattr(heuristic, "IntendedFor"):
        logger.info("Processing IntendedFor fields based on heuristic file")
        intention_map.update(heuristic.IntendedFor)
        logger.debug("Intention map: %s", intention_map)

    metadata_extras = defaultdict(list)
    if hasattr(heuristic, "MetadataExtras"):
        logger.info("Processing Medatata fields based on heuristic file")
        metadata_extras.update(heuristic.MetadataExtras)
        logger.debug("Metadata extras: %s", metadata_extras)

    if not dry_run:
        logger.info("Applying changes to files...")

    if hasattr(heuristic, "ReplaceSubject"):
        subject_rename = heuristic.ReplaceSubject
    else:
        subject_rename = None
    if hasattr(heuristic, "ReplaceSession"):
        session_rename = heuristic.ReplaceSession
    else:
        session_rename = None

    for key, val in to_rename.items():

        # assert val is list
        if not isinstance(val, set):
                val = set(val)
        for seqitem, value in enumerate(val):
            apply_heuristic(client, key, value, dry_run, intention_map[key],
                            metadata_extras[key], subject_rename, session_rename, seqitem+1)

    if not dry_run:
        for ses in sessions:
            confirm_intentions(client, ses)

def get_parser():

    parser = argparse.ArgumentParser(
        description="Use a heudiconv heuristic to curate bids on flywheel")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        nargs="+",
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
        "--dry_run",
        help="Don't apply changes",
        action='store_true',
        default=False
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

    project_label = ' '.join(args.project)
    convert_to_bids(client=fw,
                    project_label=project_label,
                    heuristic_path=args.heuristic,
                    session_labels=args.session,
                    subject_labels=args.subject,
                    dry_run=args.dry_run)


if __name__ == '__main__':
    main()
