import argparse
import warnings
import logging
import flywheel
import pandas as pd
from ..query import get_seq_info


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
        df = df.drop_duplicates(subset=['TR', 'TE', 'protocol_name', 'is_motion_corrected', 'is_derived'])
    if dry_run:
        print(df)
    else:
        df.to_csv("{}/{}_SeqInfo.tsv".format(path, project_label),
                  sep="\t", index=False)

    logger.info("Done!")


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
        "--dry_run",
        help="Don't apply changes",
        action='store_true',
        default=False
    )
    parser.add_argument(
        "--unique",
        help="Strip down to unique sequence combinations",
        default=True
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
    if args.verbose or args.dry_run:
        logger.setLevel(logging.DEBUG)

    project_label = ' '.join(args.project)
    tabulate_bids(client=fw,
                  project_label=project_label,
                  path=args.path,
                  session_labels=args.session,
                  subject_labels=args.subject,
                  dry_run=args.dry_run,
                  unique=args.unique)


if __name__ == '__main__':
    main()
