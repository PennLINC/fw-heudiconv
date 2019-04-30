import flywheel
import argparse
import os
import logging
import warnings
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bids-exporter')

def get_from_dict(dataDict, maplist):

    first, rest = maplist[0], maplist[1:]

    if rest:
        # if `rest` is not empty, run the function recursively
        return get_from_dict(dataDict[first], rest)
    else:
        return dataDict[first]


def key_exists(obj, chain):

    #https://stackoverflow.com/questions/43491287/elegant-way-to-check-if-a-nested-key-exists-in-a-python-dict
    _key = chain[0]
    if _key in obj:
        if obj[_key]:
            if len(chain) > 1:
                return key_exists(obj[_key], chain[1:])
            else:
                obj[_key]
        else:
            return None


def get_metadata(container, nested_key_list):

    if key_exists(container, nested_key_list):
        return(get_from_dict(container, nested_key_list))
    else:
        return None


def download_sidecar(d, fpath, remove_bids=True):

    if remove_bids and 'BIDS' in d:
        del d['BIDS']

    with open(fpath, 'w') as sidecar:
        output = json.dump(d, fp=sidecar, sort_keys=True, indent=4)


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

    # get dataset description file
    to_download['dataset_description'].append({
        'name': 'dataset_description.json',
        'type': 'dataset_description',
        'data': get_metadata(project_obj, ['info', 'BIDS'])
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

    for ses in sessions:
        for sf in ses.files:
            d = {
                'name': sf.name,
                'type': sf.type,
                'data': ses.id,
                'BIDS': get_metadata(sf, ['info', 'BIDS'])
            }
            to_download['session'].append(d)

    # acquistion level
    logger.info("Processing acquisition files...")
    acquisitions = [a for s in sessions for a in client.get_session_acquisitions(s.id)]
    acquisitions_meta = [a.info for a in acquisitions]
    acquisitions2 = [client.get_acquisition(acq['_id']) for acq in acquisitions]
    acquisition_files = [f for acq in acquisitions2 for f in acq.get('files')]
    for af in acquisition_files:
        d = {
            'name': af.name,
            'type': af.type,
            'data': af.parent.id,
            'BIDS': get_metadata(af, ['info', 'BIDS']),
            'sidecar': get_metadata(af, ['info'])
        }
        if bool(d['BIDS']) and d['BIDS'] != "NA":
            to_download['acquisition'].append(d)

    return to_download


def download_bids(client, to_download, root_path, folders_to_download = ['anat', 'dwi', 'func', 'fmap']):

    logger
    # handle dataset description
    if to_download['dataset_description']:
        description = to_download['dataset_description'][0]

        path = "/".join([root_path, description['name']])
        print(path)
        download_sidecar(description['data'], path, remove_bids=False)

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

        project_path = get_metadata(fi, ['BIDS', 'Path'])
        folder = get_metadata(fi, ['BIDS', 'Folder'])
        ignore = get_metadata(fi, ['BIDS', 'ignore'])

        if project_path and folder in folders_to_download and not ignore and 'sidecar' in fi:
            fname = get_metadata(fi, ['BIDS', 'Filename'])
            extensions = ['nii.gz', 'bval', 'bvec']
            sidecar_name = fname
            for x in extensions:
                sidecar_name = sidecar_name.replace(x, 'json')

            download_path = '/'.join([root_path, project_path])
            file_path = '/'.join([download_path, fname])
            sidecar_path = '/'.join([download_path, sidecar_name])
            print(fi['name'])
            print(file_path)
            print(sidecar_path)
            acq = client.get(fi['data'])
            print(acq.label)

            if not os.path.exists(download_path):
                os.makedirs(download_path)
            acq.download_file(fi['name'], file_path)
            download_sidecar(fi['sidecar'], sidecar_path, remove_bids=True)


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
        "--path",
        help="The target directory to download",
        required=True,
        default="."
    )
    parser.add_argument(
        "--subject",
        help="The subject to curate",
        default=None,
        type=str
    )
    parser.add_argument(
        "--session",
        help="The session to curate",
        default=None,
        type=str
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

    download_bids(client=fw, to_download=downloads, root_path=args.path)

if __name__ == '__main__':
    main()
