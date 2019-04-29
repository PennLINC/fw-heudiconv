import flywheel
import argparse
import os
import logging


logging.basicConfig(level=logging.INFO)


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
            return key_exists(obj[_key], chain[1:]) if len(chain) > 1 else obj[_key]
        else:
            return None


def get_metadata(container, nested_key_list):

    if key_exists(container, nested_key_list):
        return(get_from_dict(container, nested_key_list))
    else:
        return None


def gather_bids(client, project_label, subject_labels=None, session_labels=None):
    '''
    {
    'name': container.filename,
    'path': path,
    'type': type of file,
    'data': container}
    '''

    to_download = {
        'project': [],
        'session': [],
        'acquisition': []
    }

    # project level
    project_obj = client.projects.find_first('label="{}"'.format(project_label))

    # get dataset description file
    to_download['project'].append({
        'name': 'dataset_description.json',
        'type': 'dataset_description',
        'data': get_metadata(project_obj, ['info', 'BIDS'])
    })
    # download any project level files
    project_files = project_obj.files
    for pf in project_files:
        d = {
            'name': pf.name,
            'type': 'attachment',
            'data': project_obj.id
        }
        to_download['project'].append(d)

    # session level
    sessions = client.get_project_sessions(project_obj.id)

    # filters
    #if session_labels:
    #    sessions = [s for s in sessions if s.label in session_labels]
    #if subject_labels:
    #    for ses in sessions:
    #        subject = client.get(ses.parents['subject'])

    for ses in sessions:
        for sf in ses.files:
            d = {
                'name': sf.name,
                'type': sf.type,
                'data': ses.id,
                'BIDS': get_metadata(sf, ['info', 'BIDS'])
            }
            to_download['session'].append(d)

    # session level
    acquisitions = [a for s in sessions for a in client.get_session_acquisitions(s.id)]
    acquisitions_meta = [a.info for a in acquisitions]
    acquisitions2 = [client.get_acquisition(acq['_id']) for acq in acquisitions]
    acquisition_files = [f for acq in acquisitions2 for f in acq.get('files')]
    for af in acquisition_files:
        d = {
            'name': af.name,
            'type': af.type,
            'data': get_metadata(af, ['origin', 'id']),
            'BIDS': get_metadata(af, ['info', 'BIDS']),
            'sidecar': get_metadata(af, ['info'])
        }
        if bool(d['BIDS']):
            to_download['acquisition'].append(d)

    return to_download

def download_bids(to_download, root_path):

    # deal with project level files
    # NOT YET IMPLEMENTED
    for fi in to_download['project']:

        download_path = get_metadata(fi, ['BIDS', 'Path'])
        if download_path:
            print('/'.join([root_path, download_path, fi['name']]))

    # deal with session level files
    # NOT YET IMPLEMENTED
    for fi in to_download['session']:
        pass
        #download_path = get_metadata(fi, ['BIDS', 'Path'])
        #if download_path:
        #    print('/'.join([root_path, download_path, fi['name']]))

    # deal with acquisition level files
    for fi in to_download['acquisition']:

        download_path = get_metadata(fi, ['BIDS', 'Path'])
        if download_path:
            print('/'.join([root_path, download_path, fi['name']]))
            print(bool(fi['sidecar']))


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
        help="The project in flywheel",
        nargs="+",
        required=True,
        default="."
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
    assert os.path.isdir(args.path), "Path does not exist!"
    gather_bids(client=fw,
                    project_label=project_label,
                    session_label=args.session,
                    subject_code=args.subject,
                    verbose=args.verbose)

if __name__ == '__main__':
    main()
