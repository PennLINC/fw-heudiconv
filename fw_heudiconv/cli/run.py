import argparse
import warnings
import flywheel


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
        help="Path to a heudiconv-style heurisric file"
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
    project = ' '.join(args.project)
