import argparse
import warnings
import flywheel
from ..convert import apply_heuristic, update_intentions
from ..query import get_sessions, get_seq_info
from heudiconv import utils


def convert_to_bids(client, project_label, heuristic_path, subject_code=None, session_label=None, verbose=True):
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
    """

    if verbose: print("Querying Flywheel server...")
    sessions = get_sessions(client, project_label, subject=subject_code, session=session_label)
    seq_infos = get_seq_info(client, project_label, sessions)
    if verbose: print("Loading heuristic file...")
    heuristic = utils.load_heuristic(heuristic_path)
    BIDS_objects = {}
    if verbose: print("Applying heuristic to query results...")
    to_rename = heuristic.infotodict(seq_infos)
    if verbose: print("Applying changes to files...")
    for key, val in to_rename.items():
        apply_heuristic(client, key, val)
    for s in sessions:
        update_intentions(s)


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
        help="The name of the subject",
        default=None
    )
    parser.add_argument(
        "--session",
        help="The session to curate",
        default=None
    )
    parser.add_argument(
        "--verbose",
        help="Print ongoing messages of progress",
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
    project_label = ' '.join(args.project)
    convert_to_bids(client=fw,
                    project_label=project_label,
                    heuristic_path=args.heuristic,
                    session_label=args.session,
                    subject_code=args.subject,
                    verbose=args.verbose)

if __name__ == '__main__':
    main()
