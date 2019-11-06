import argparse
import flywheel
import logging
import warnings
import sys

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from fw_heudiconv.cli.export import get_nested


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-clearer')


def clear_bids(client, project_label, session_labels=None, subject_labels=None, dry_run=False,
               file_types = ['.nii', '.bval', '.bvec']):

    logger.info("Querying Flywheel server...")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        project_obj = client.projects.find_first('label="{}"'.format(project_label))

    if project_obj is None:
        logger.error("Project not found! Maybe check spelling...?")
        return 1

    logger.debug('\tFound project: \n\t\t%s (%s)', project_obj['label'], project_obj.id)
    sessions = client.get_project_sessions(project_obj.id)

    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label'] in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]

    if not sessions:
        logger.error("No sessions found!")
        return 1

    logger.info('\tFound subjects:\n\t\t%s',
                 "\n\t\t".join(set(['%s (%s)' % (ses.subject.label, ses.subject.id) for ses in sessions])))

    logger.info('\tFound sessions:\n\t\t%s',
                 "\n\t\t".join(['%s (%s)' % (ses['label'], ses.id) for ses in sessions]))

    file_list = []
    for ses in sessions:

        acquisitions = ses.acquisitions()

        for acq in acquisitions:

            files = [f.to_dict() for f in acq.files if any([x in f.name for x in file_types])]

            files = [f for f in files if get_nested(f, 'info', 'BIDS') != 'NA' and get_nested(f, 'info', 'BIDS') is not None and get_nested(f, 'info', 'BIDS', 'Filename') != '']

            if files:
                file_list.append({acq.id: files})

    fnames = []
    for x in file_list:
        for k, v in x.items():
            for u in v:
                name = get_nested(u, 'info', 'BIDS', 'Filename')
                if name is not None:
                    fnames.append(name)

    if file_list:
        logger.debug("This will remove BIDS data from %d files:\n\t%s" % (len(file_list), "\n\t".join([x for x in fnames])))


        if not dry_run:
            logger.info('\t\t=======: Removing BIDS data :=======\n')

            for acq_files in file_list:

                for k, v in acq_files.items():
                    acq = client.get(k)

                    for fi in v:

                        BIDS = get_nested(fi, 'info', 'BIDS')
                        new_bids = {k:'' for k,v in BIDS.items()}
                        acq.update_file_info(fi['name'], {'BIDS': new_bids})

        else:
            logger.info("Disable `dry_run` mode to apply these changes and remove the BIDS information.")

    else:
        logger.info("No BIDS data to remove! (That was easy...)")

    return 0


def get_parser():

    parser = argparse.ArgumentParser(
        description="Go nuclear: clear BIDS data from Flywheel")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        nargs="+",
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

    logger.info("{:=^70}\n".format(": fw-heudiconv clearer starting up :"))
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

    project_label = ' '.join(args.project)
    status = clear_bids(client=fw,
                    project_label=project_label,
                    session_labels=args.session,
                    subject_labels=args.subject,
                    dry_run=args.dry_run)

    logger.info("Done!")
    logger.info("{:=^70}".format(": Exiting fw-heudiconv clearer :"))
    sys.exit(status)

if __name__ == '__main__':
    main()
