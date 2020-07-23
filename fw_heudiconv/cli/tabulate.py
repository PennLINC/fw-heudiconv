import argparse
import warnings
import logging
import flywheel
import pandas as pd
from fw_heudiconv.backend_funcs.query import get_seq_info


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-tabulator')


def tabulate_bids(client, project_label, path=".", subject_labels=None,
                  session_labels=None, dry_run=False, unique=True):
    """Writes out a tabular form of the Seq Info objects

    Args:
        client (Client): The flywheel sdk client
        project_label (str): The label of the project
        heuristic_path (str): The path to the heuristic file or the name of a
            known heuristic
        subject_code (str): The subject code
        session_label (str): The session label
        dry_run (bool): Print the changes, don't apply them on flywheel
    """

    logger.info("Querying Flywheel server...")
    project_obj = client.projects.find_first('label="{}"'.format(project_label))
    assert project_obj, "Project not found! Maybe check spelling...?"

    logger.debug('Found project: %s (%s)', project_obj['label'], project_obj.id)
    sessions = client.get_project_sessions(project_obj.id)
    assert sessions, "No sessions found!"

    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label'] in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]
    logger.debug('Found sessions:\n\t%s',
                 "\n\t".join(['%s (%s)' % (ses['label'], ses.id) for ses in sessions]))

    # Find SeqInfos to apply the heuristic to
    seq_infos = get_seq_info(client, project_label, sessions)
    seq_info_dicts = [seq._asdict() for seq in seq_infos]
    df = pd.DataFrame.from_dict(seq_info_dicts)

    if unique:
        df = df.drop_duplicates(subset=['TR', 'TE', 'protocol_name', 'is_motion_corrected', 'is_derived', 'series_description'])
        df = df.drop(['total_files_till_now', 'dcm_dir_name'], 1)

    return df


def output_result(df, path, project_label, dry_run):

    if dry_run:
        print(df)
    else:
        df.to_csv("{}/{}_SeqInfo.tsv".format(path, project_label),
                  sep="\t", index=False)


def get_parser():

    parser = argparse.ArgumentParser(
        description="Tabulate DICOM header info from a project on Flywheel")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        required=True
    )
    parser.add_argument(
        "--path",
        help="Path to download .tsv file",
        default=".",
        required=False
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
    unique = parser.add_mutually_exclusive_group()

    unique.add_argument(
        '--unique',
        dest='unique',
        action='store_true'
    )
    unique.add_argument(
        '--no-unique',
        dest='unique',
        action='store_false'
    )
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )

    return parser


def main():

    logger.info("{:=^70}\n".format(": fw-heudiconv tabulator starting up :"))

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
    if args.verbose or args.dry_run:
        logger.setLevel(logging.DEBUG)

    result = tabulate_bids(client=fw,
                  project_label=args.project,
                  path=args.path,
                  session_labels=args.session,
                  subject_labels=args.subject,
                  dry_run=args.dry_run,
                  unique=args.unique)

    output_result(result, path=args.path, project_label=args.project, dry_run=args.dry_run)

    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv tabulator :"))

if __name__ == '__main__':
    main()
