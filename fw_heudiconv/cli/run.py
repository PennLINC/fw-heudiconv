import argparse
import warnings
import ast
import flywheel
import pandas as pd
from ..query import query
from heudiconv import utils


def convert_to_bids(client, project_label, heuristic_path, subject_code=None, session_label=None):
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
    seq_infos = query(client, project_label, subject=subject_code,
                      session=session_label)
    heuristic = utils.load_heuristic(heuristic_path)
    BIDS_objects = {}
    to_rename = heuristic.infotodict(seq_infos)
    errors = apply_conversion(to_rename, subject_code, session_label, verbose=True)
    print(pd.DataFrame(errors))


def apply_conversion(client, to_rename, subj_label=None, sess_label=None, verbose=True):
    """docstring docstring docstring
    """


    intended = []
    suffixes = {'nifti': ".nii.gz", 'bval': ".bval", 'bvec': ".bvec"}
    ftypes = ['nifti', 'bval', 'bvec']
    FAILS = []
    all_acquisitions = [client.get(val[0]) for _, val in to_rename.items() if val]

    # get subj and sess labels if not set
    if subj_label is None:
        subj_label = client.get(all_acquisitions[0].parents['subject']).label
    if sess_label is None:
        sess_label = client.get(all_acquisitions[0].parents['session']).label

    for key, val in to_rename.items():
        if val is None:
            continue

        # make a bids dictionary
        bids_keys = ['sub', 'ses', 'folder', 'name']
        bids_vals = key[0].format(subject=subj_label, session="ses-"+sess_label).split("/")
        bids_dict = dict(zip(bids_keys, bids_vals))

        # get the acquisition object
        acq_id = val[0]
        try:
            acq = client.get(acq_id)
            files = [f for f in acq.files if f.type in ftypes]
        except Exception as e:
            print("Could not query flywheel to apply BIDS changes!")
            print(e)
            error = {'subject': subj_label,
                     'session': sess_label,
                     'job': 'query files',
                     'reason': e}
            FAILS.append(error)
            continue

        for f in files:
            print("old bids:")
            print(f.info['BIDS'])

            # special check for magnitude files
            if "e1.nii.gz" in f.name:
                suffix = "1" + suffixes[f.type]
            elif "e2.nii.gz" in f.name:
                suffix = "2" + suffixes[f.type]
            else:
                suffix = suffixes[f.type]

            if verbose:
                print()
                print(f.name)
                print("new bids:")

            try:
                new_bids = f.info['BIDS']
                new_bids['Filename'] = bids_dict['name']+suffix
                new_bids['Folder'] = bids_dict['folder']
                new_bids['Path'] = "/".join([bids_dict['sub'],
                                            bids_dict['ses'],
                                            bids_dict['folder']])
                new_bids['error_message'] = ""
                new_bids['valid'] = True
            except Exception as e:
                print("Couldn't find BIDS data for file ", f.name)
                print("Maybe BIDS curation hasn't been run...?")
                print(e)
                error = {'subject': subj_label,
                         'session': sess_label,
                         'job': 'query files',
                         'reason': e}
                FAILS.append(error)

            if verbose: print(new_bids)

            try:
                acq.update_file_info(f.name, {'BIDS': new_bids})
            except Exception as e:
                print("Unable to update file ", f.name)
                print(e)
                error = {'subject': subj_label,
                         'session': sess_label,
                         'job': 'update file',
                         'reason': e}
                FAILS.append(error)
                continue

            # track intention updates
            if "IntendedFor" in new_bids and bool(new_bids['IntendedFor']):
                intended.append((key, val))

    # update file intentions for each intended
    # get all of the files
    all_files = []

    for acq in all_acquisitions:
        for f in acq.files:
            if f.type in ['nifti', 'bval', 'bvec']:
                all_files.append(f)

    # loop over the intented files
    if intended:
        for key, val in intended:

            acq_id = val[0]
            try:
                acq = client.get(acq_id)
                acquisition_files = [f for f in acq.files if f.type in ftypes]
            except Exception as e:
                print("Could not query flywheel to apply intentions!")
                print(e)
                error = {'subject': subj_label, 'session': sess_label, 'job': 'query files', 'reason': e}
                FAILS.append(error)
                continue

            if verbose: print("For acquisition: ", acq.label)

            # (have to update each file in the acquisition)
            for f in acquisition_files:
                intent = [x["Folder"] for x in ast.literal_eval(f.info['BIDS']['IntendedFor'])]
                if verbose: print("Intended For: ", intent)

                # loop through all files and add any with matching intent to target files
                target_files = []

                for g in all_files:
                    if g.info['BIDS']['Folder']:
                        if g.info['BIDS']['Folder'] in intent:

                            # build appropriate bids name for intention path
                            path = key[0].format(subject=subj_label, session="ses-"+sess_label).split("/")[1]
                            path = "/".join([path, g.info['BIDS']['Folder'], g.info['BIDS']['Filename']])
                            target_files.append(path)

                if verbose: print(target_files)

                try:
                    acq.update_file_info(f.name, {'IntendedFor': target_files})
                except Exception as e:
                    print("Unable to update intentions", f.name)
                    print(e)
                    error = {'subject': subj_label, 'session': sess_label, 'job': 'update intentions', 'reason': e}
                    FAILS.append(error)
                    continue


    if verbose: print("Updates complete")
    return(FAILS)

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
        "--subject",
        help="The name of the subject to curate",
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
    convert_to_bids(fw, project_label, args.heuristic, args.verbose)
