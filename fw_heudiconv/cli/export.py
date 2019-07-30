import flywheel
import argparse
import os
import logging
import warnings
import json
import shutil
import re
import csv
from pathlib import Path
from ..query import print_directory_tree


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-exporter')


def get_nested(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError):
            return None
    return dct


def download_sidecar(d, fpath, remove_bids=True):

    if remove_bids and 'BIDS' in d:
        if 'Task' in d['BIDS']:
            if d['BIDS']['Task'] != "":
                d['TaskName'] = d['BIDS']['Task']
        del d['BIDS']

    with open(fpath, 'w') as sidecar:
        json.dump(d, fp=sidecar, sort_keys=True, indent=4)

def check_tasks(root_path):

    paths = [os.path.join(x[0], y) for x in os.walk(root_path) for y in x[2]]
    paths = [x for x in paths if 'func' in x and 'rest' not in x]

    if not paths:
        logger.info("No task events in this bids dataset.")
        return

    niftis = [x for x in paths if '.nii.gz' in x]
    tsvs = [x for x in paths if '.tsv' in x]

    if not tsvs:
        logger.warning("No events.tsv found in func folder; creating empty TSVs")
        for nii in niftis:
            path = re.sub(r'(?<=_)[a-zA-Z]+\.nii\.gz', 'events.tsv', nii)
            with open(str(path), "wt") as f:
                tsv_writer = csv.writer(f, delimiter='\t')
                tsv_writer.writerow(['onset', 'duration'])

    else:
        for nii in niftis:
            shortened = re.sub(r'(?<=_)[a-zA-Z]+\.nii\.gz', '', nii)
            has_matching_tsv = False
            for t in tsvs:
                if shortened in t:
                    has_matching_tsv = True
                    continue
            if not has_matching_tsv:
                logger.warning("No events.tsv found for {}; creating empty TSV".format(shortened))
                path = shortened + 'events.tsv'
                with open(str(path), "wt") as f:
                    tsv_writer = csv.writer(f, delimiter='\t')
                    tsv_writer.writerow(['onset', 'duration'])



def gather_bids(client, project_label, subject_labels=None, session_labels=None):
    '''
    {
    'name': container.filename,
    'path': path,
    'type': type of file,
    'data': container}
    '''
    logger.info("Gathering bids data:")

    to_download = {
        'dataset_description': [],
        'project': [],
        'session': [],
        'acquisition': []
    }

    # dataset description
    project_obj = client.projects.find_first('label="{}"'.format(project_label))
    assert project_obj, "Project not found! Maybe check spelling...?"

    # get dataset description file
    to_download['dataset_description'].append({
        'name': 'dataset_description.json',
        'type': 'dataset_description',
        'data': get_nested(project_obj, 'info', 'BIDS')
    })
    # download any project level files
    logger.info("Processing project files...")
    project_files = project_obj.files
    for pf in project_files:
        d = {
            'name': pf.name,
            'type': 'attachment',
            'data': project_obj.id
        }
        to_download['project'].append(d)

    # session level
    logger.info("Processing session files...")
    sessions = client.get_project_sessions(project_obj.id)

    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label'] in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]
    assert sessions, "No sessions found!"
    for ses in sessions:
        for sf in ses.files:
            d = {
                'name': sf.name,
                'type': sf.type,
                'data': ses.id,
                'BIDS': get_nested(sf, 'info', 'BIDS')
            }
            to_download['session'].append(d)

    # acquistion level
    logger.info("Processing acquisition files...")
    acquisitions = [a for s in sessions for a in client.get_session_acquisitions(s.id)]
    acquisitions2 = [client.get_acquisition(acq['_id']) for acq in acquisitions]
    acquisition_files = [f for acq in acquisitions2 for f in acq.get('files')]
    for af in acquisition_files:
        d = {
            'name': af.name,
            'type': af.type,
            'data': af.parent.id,
            'BIDS': get_nested(af, 'info', 'BIDS'),
            'sidecar': get_nested(af, 'info')
        }
        if any(x in d['name'] for x in ['bval', 'bvec']):
            del d['sidecar']
        if d['BIDS'] and d['BIDS'] != "NA":
            to_download['acquisition'].append(d)
    return to_download


def download_bids(client, to_download, root_path, folders_to_download = ['anat', 'dwi', 'func', 'fmap'], dry_run=True):

    if dry_run:
        logger.info("Preparing output directory tree...")
    else:
        logger.info("Downloading files...")
    root_path = "/".join([root_path, "bids_dataset"])
    Path(root_path).mkdir()
    # handle dataset description
    if to_download['dataset_description']:
        description = to_download['dataset_description'][0]

        path = "/".join([root_path, description['name']])

        if dry_run:
            Path(path).touch()
        else:
            download_sidecar(description['data'], path, remove_bids=False)

    # write bids ignore
    if not any(x['name'] == '.bidsignore' for x in to_download['project']):
        # write bids ignore
        path = "/".join([root_path, ".bidsignore"])
        ignored_modalities = ['asl/\n', 'qsm/\n']
        if dry_run:
            Path(path).touch()
        else:
            with open(path, 'w') as bidsignore:
                bidsignore.writelines(ignored_modalities)

    # deal with project level files
    # NOT YET IMPLEMENTED
    for fi in to_download['project']:
        pass
        #download_path = get_metadata(fi, ['BIDS', 'Path'])
        #if download_path:
        #    print('/'.join([root_path, download_path, fi['name']]))

    # deal with session level files
    # NOT YET IMPLEMENTED
    for fi in to_download['session']:
        pass
        #download_path = get_metadata(fi, ['BIDS', 'Path'])
        #if download_path:
        #    print('/'.join([root_path, download_path, fi['name']]))

    # deal with acquisition level files
    for fi in to_download['acquisition']:
        project_path = get_nested(fi, 'BIDS', 'Path')
        folder = get_nested(fi, 'BIDS', 'Folder')
        ignore = get_nested(fi, 'BIDS', 'ignore')

        if project_path and folder in folders_to_download and not ignore:

            # only download files with sidecars
            if 'sidecar' in fi:
                fname = get_nested(fi, 'BIDS', 'Filename')
                extensions = ['nii.gz', 'bval', 'bvec']
                sidecar_name = fname
                for x in extensions:
                    sidecar_name = sidecar_name.replace(x, 'json')

                download_path = '/'.join([root_path, project_path])
                file_path = '/'.join([download_path, fname])
                sidecar_path = '/'.join([download_path, sidecar_name])
                acq = client.get(fi['data'])

                if not os.path.exists(download_path):
                    os.makedirs(download_path)

                if dry_run:
                    Path(file_path).touch()
                    Path(sidecar_path).touch()
                else:
                    acq.download_file(fi['name'], file_path)
                    download_sidecar(fi['sidecar'], sidecar_path, remove_bids=True)

            #exception: it may be an events tsv
            elif any(x in fi['name'] for x in ['bval', 'bvec', 'tsv']):
                fname = get_nested(fi, 'BIDS', 'Filename')
                download_path = '/'.join([root_path, project_path])
                file_path = '/'.join([download_path, fname])
                acq = client.get(fi['data'])

                if not os.path.exists(download_path):
                    os.makedirs(download_path)

                if dry_run:
                    Path(file_path).touch()
                    Path(sidecar_path).touch()
                else:
                    acq.download_file(fi['name'], file_path)
    check_tasks(root_path)

    logger.info("Done!")
    print_directory_tree(root_path)
    if dry_run:
        shutil.rmtree(root_path)


def get_parser():

    parser = argparse.ArgumentParser(
        description="Export BIDS compliant data")
    parser.add_argument(
        "--project",
        help="The project in flywheel",
        nargs="+",
        required=True
    )
    parser.add_argument(
        "--path",
        help="The target directory to download",
        required=True,
        default="."
    )
    parser.add_argument(
        "--subject",
        help="The subject to curate",
        nargs="+",
        default=None,
        type=str
    )
    parser.add_argument(
        "--session",
        help="The session to curate",
        nargs="+",
        default=None,
        type=str
    )
    parser.add_argument(
        "--folders",
        help="The BIDS folders to download",
        nargs="+",
        default=['anat', 'dwi', 'fmap', 'func']
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
    project_label = ' '.join(args.project)
    assert os.path.exists(args.path), "Path does not exist!"
    downloads = gather_bids(client=fw,
                            project_label=project_label,
                            session_labels=args.session,
                            subject_labels=args.subject)

    download_bids(client=fw, to_download=downloads, root_path=args.path, folders_to_download=args.folders, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
