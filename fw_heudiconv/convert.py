import os
import ast
import json
import logging

logger = logging.getLogger('fwHeuDiConv-curator')

def build_intention_path(f):
    """Builds a string of the path to the file w.r.t. subject dir
    """
    fname = f.info["BIDS"]["Filename"]
    folder = f.info["BIDS"]["Folder"]
    ses = fname.split("_")[1]
    return("/".join([ses, folder, fname]))


def update_intentions(client, session):
    """Updates the IntendedFor field of all files in a session with intentions

    Fieldmap scans need to be pointed toward the scans they map; this function
    loops through files in a session, and if it is a fieldmap/has a folder that
    it's intended for, finds any files in the folder and builds a list of paths

    Args:
        client (Client): The flywheel sdk client
        session (obj): The flywheel session object
    """
    ftypes = ['nifti', 'bval', 'bvec']
    files = [f for acq in session.acquisitions() for f in acq.files if f.type in ftypes]

    for f in files:
        if 'BIDS' in f.info:
            if 'IntendedFor' in f.info['BIDS']:
                if f.info['BIDS']["IntendedFor"]:
                    try:
                        folder = [x["Folder"] for x in
                                  ast.literal_eval(f.info['BIDS']['IntendedFor'])]
                    except Exception as e:
                        logger.warning(e)
                        continue
                    target_files = [g for g in files if g.info['BIDS']['Folder'] in folder]
                    target_files = [build_intention_path(g) for g in target_files]

                    f.parent.update_file_info(f.name, {"IntendedFor": target_files})


def apply_heuristic(client, heur, acquisition_ids, dry_run=False, intended_for=[]):
    """ Apply heuristic to rename files

    This function applies the specified heuristic to the files given in the
    list of acquisitions.

    Args:
        client (Client): The flywheel sdk client
        heur (tuple): 3-tuple, the "key" of a seq_info dictionary, where
            the first item of the tuple is the naming convention as a string
        acquisition_ids (list): The "value" of a seq_info dictionary, the list
            of acquisitions to which the naming convention applies
    """
    suffixes = {'nifti': ".nii.gz", 'bval': ".bval", 'bvec': ".bvec"}
    ftypes = ['nifti', 'bval', 'bvec', 'tsv']
    template, outtype, annotation_classes = heur

    for acq in set(acquisition_ids):

        acquisition_object = client.get(acq)
        sess_label = client.get(acquisition_object.parents.session).label
        subj_label = client.get(acquisition_object.parents.subject).label

        files = [f for f in acquisition_object.files if f.type in ftypes]
        bids_keys = ['sub', 'ses', 'folder', 'name']
        ses_fmt = sess_label if sess_label.startswith("ses-") else "ses-" + sess_label

        for fnum, f in enumerate(files):
            bids_vals = template.format(subject=subj_label, session=ses_fmt, item=fnum+1).split("/")
            bids_dict = dict(zip(bids_keys, bids_vals))
            suffix = suffixes[f.type]

            if 'BIDS' not in f.info:
                f.info['BIDS'] = ""
            new_bids = f.info['BIDS']
            if new_bids == "NA" or new_bids == "":
                new_bids = add_empty_bids_fields(bids_dict['folder'], bids_dict['name'])
            new_bids['Filename'] = bids_dict['name']+suffix
            new_bids['Folder'] = bids_dict['folder']
            new_bids['Path'] = "/".join([bids_dict['sub'],
                                         bids_dict['ses'],
                                         bids_dict['folder']])
            new_bids['error_message'] = ""
            new_bids['valid'] = True
            if dry_run:
                print(f.name, "->", new_bids["Path"] + "/" + new_bids['Filename'])
            else:
                acquisition_object.update_file_info(f.name, {'BIDS': new_bids})


def add_empty_bids_fields(folder, fname=None):

    if "fmap" in folder:
        if not fname:
            print("No filename given, can't set intentions for this fieldmap!")
        elif "epi" in fname:
            IntendedFor = "[{'Folder': 'dwi'}]"
            Modality = "epi"
        else:
            IntendedFor = "[{'Folder': 'func'}]"
            Modality = "fieldmap"
        new_bids = {"Acq": "",
                    "Ce": "",
                    "Dir": "",
                    "Echo": "",
                    "error_message": "",
                    "Filename": "",
                    "Folder": "fmap",
                    "ignore": "",
                    "IntendedFor": IntendedFor,
                    "Mod": "",
                    "Modality": Modality,
                    "Path": "",
                    "Rec": "",
                    "Run": "",
                    "Task": "",
                    "template": "fieldmap_file",
                    "valid": False}

    elif "dwi" in folder:

        new_bids = {"Acq": "",
                    "Ce": "",
                    "Dir": "",
                    "Echo": "",
                    "error_message": "",
                    "Filename": "",
                    "Folder": "",
                    "ignore": "",
                    "IntendedFor": "",
                    "Mod": "",
                    "Modality": "dwi",
                    "Path": "",
                    "Rec": "",
                    "Run": "",
                    "Task": "",
                    "template": "diffusion_file",
                    "valid": False}

    elif "func" in folder:

        new_bids = {"Acq": "",
                    "Ce": "",
                    "Dir": "",
                    "Echo": "",
                    "error_message": "",
                    "Filename": "",
                    "Folder": "",
                    "ignore": "",
                    "IntendedFor": "",
                    "Mod": "",
                    "Modality": "",
                    "Path": "",
                    "Rec": "",
                    "Run": "",
                    "Task": "",
                    "template": "",
                    "valid": False}

    elif "anat" in folder:

        new_bids = {"Acq": "",
                    "Ce": "",
                    "Dir": "",
                    "Echo": "",
                    "error_message": "",
                    "Filename": "",
                    "Folder": "anat",
                    "ignore": "",
                    "IntendedFor": "",
                    "Mod": "",
                    "Modality": "T1w",
                    "Path": "",
                    "Rec": "",
                    "Run": "",
                    "Task": "",
                    "template": "anat_file",
                    "valid": False}

    else:

        new_bids = {"Acq": "",
                    "Ce": "",
                    "Dir": "",
                    "Echo": "",
                    "error_message": "",
                    "Filename": "",
                    "Folder": "",
                    "ignore": "",
                    "IntendedFor": "",
                    "Mod": "",
                    "Modality": "",
                    "Path": "",
                    "Rec": "",
                    "Run": "",
                    "Task": "",
                    "template": "",
                    "valid": False}

    return(new_bids)
