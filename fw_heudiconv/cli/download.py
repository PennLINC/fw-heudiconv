import flywheel
import argparse
from ..query import get_sessions


def get_bids_metadata(container):

    if container.info['BIDS']:
        if not container.info['BIDS']['ignore']:
            return container.info['BIDS']


def download_bids(client, project_label, subject_label=None, session_label=None):

    project_obj = client.
    sessions = get_project_sessions()
    sessions_meta = [get_bids_metadata(s) for s in sessions]
    acquisitions = [a for s in sessions for a in client.get_session_acquisitions(s.id)]
    acquisitions_meta = [get_bids_metadata(a) for a in acquisitions]
    files = [f for acq in acquisitions for f in acq.get('files')]

    return

def get_parser():

    parser = argparse.ArgumentParser(
        description="Export BIDS compliant data curated with fw-heudiconv")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        nargs="+",
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
    download_bids(client=fw,
                    project_label=project_label,
                    session_label=args.session,
                    subject_code=args.subject,
                    verbose=args.verbose)

if __name__ == '__main__':
    main()
