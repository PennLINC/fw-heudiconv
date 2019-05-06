import flywheel
import argparse
import os
import logging
import warnings
import json
import anytree
from anytree import Node, RenderTree, AsciiStyle


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fwHeuDiConv-exporter')


# def print_directory_tree(downloads_dict, folders_to_download=['anat', 'dwi', 'func', 'fmap']):
#
#     proj_dir = Node(downloads_dict['dataset_description'][0]['data']['Name'])
#     # project attachments NOT YET IMPLEMENTED
#     #project_files = [Node(f) for f in downloads_dict['project'] if get_nested(f, 'BIDS', 'Folder')]
#     # session attachments NOT YET IMPLEMENTED
#     #session_files = [f for f in downloads_dict['session'] if get_nested(f, 'BIDS', 'Folder')]
#
#     paths = [get_nested(f, 'BIDS', 'Path').split("/") for f in downloads_dict['acquisition'] if get_nested(f, 'BIDS', 'Folder') in folders_to_download]
#     acquisition_files = [get_nested(f, 'BIDS', 'Filename') for f in downloads_dict['acquisition'] if get_nested(f, 'BIDS', 'Folder') in folders_to_download]
#
#     for i, x in enumerate(paths):
#         x.append(acquisition_files[i])
#
#     for p in paths:
#         for x in p:
#
#             if not anytree.search.find(proj_dir, lambda node: node.name == p[0]):
#                 subject = Node(p[0], parent = proj_dir)
#             if not anytree.search.find(proj_dir, lambda node: node.name == p[1]):
#                 session = Node(p[1], parent = subject)
#             if not anytree.search.find(proj_dir, lambda node: node.name == p[2]):
#                 folder = Node(p[2], parent = session)
#             if not anytree.search.find(proj_dir, lambda node: node.name == p[3]):
#                 file = Node(p[3], parent = folder)
#
#
#     print(RenderTree(proj_dir, style=AsciiStyle()).by_attr())


def get_from_dict(dataDict, maplist):

    first, rest = maplist[0], maplist[1:]

    if rest:
        # if `rest` is not empty, run the function recursively
        return get_from_dict(dataDict[first], rest)
    else:
        return dataDict[first]


def get_metadata(container, nested_key_list):

    try:
        return(get_from_dict(container, nested_key_list))
    except:
        return None


def get_nested(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct


def download_sidecar(d, fpath, remove_bids=True):

    if remove_bids and 'BIDS' in d:
        del d['BIDS']

    with open(fpath, 'w') as sidecar:
        json.dump(d, fp=sidecar, sort_keys=True, indent=4)


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
    acquisitions_meta = [a.info for a in acquisitions]
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
        if d['BIDS'] and d['BIDS'] != "NA":
            to_download['acquisition'].append(d)
    return to_download


def download_bids(client, to_download, root_path, folders_to_download = ['anat', 'dwi', 'func', 'fmap']):

    logger.info("Downloading files...")
    # handle dataset description
    if to_download['dataset_description']:
        description = to_download['dataset_description'][0]

        path = "/".join([root_path, description['name']])

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
        project_path = get_nested(fi, 'BIDS', 'Path')
        folder = get_nested(fi, 'BIDS', 'Folder')
        ignore = get_nested(fi, 'BIDS', 'ignore')

        if project_path and folder in folders_to_download and not ignore and 'sidecar' in fi:
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
            acq.download_file(fi['name'], file_path)
            download_sidecar(fi['sidecar'], sidecar_path, remove_bids=True)

    logger.info("Done!")


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
        default=['anat', 'dwi', 'fmap', 'func'],
        type=list
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

    if not args.dry_run:
        download_bids(client=fw, to_download=downloads, root_path=args.path, folders_to_download = args.folders)
    else:
        pass
        #print_directory_tree(downloads, args.folders)

if __name__ == '__main__':
    main()
