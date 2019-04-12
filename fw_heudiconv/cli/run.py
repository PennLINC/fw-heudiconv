import argparse
import warnings
import flywheel

from heudiconv import utils

import query


def convert_to_bids(client, project_label, heuristic_path, subject_code,
                    session_label):
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
    seq_infos = query.query(client, project_label, subject=subject_code,
                            session=session_label)
    heuristic = utils.load_heuristic(heuristic_path)
    BIDS_objects = {}
    for session_id, seq_info in seq_infos.items():
        ids = heuristic.infotoids(seq_infos.keys())
        info = heuristic.infotodict(seq_infos.keys())


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
        help="Path to a heudiconv-style heuristic file"
    )
    parser.add_argument(
        "--subject",
        help="The name of the subject"
    )
    parser.add_argument(
        "--subject",
        help="The name of the subject to curate"
    )
    parser.add_argument(
        "--session",
        help="The session to curate"
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
    convert_to_bids(fw, project_label, args.heuristic)

