import os
import ast
import json
import logging
import re
import operator
import re
import traceback
from .cli.export import get_nested

logger = logging.getLogger('fwHeuDiConv-curator')

def build_intention_path(f):
    """Builds a string of the path to the file w.r.t. subject dir
    """
    fname = f.info["BIDS"]["Filename"]
    folder = f.info["BIDS"]["Folder"]
    ses = fname.split("_")[1]
    return("/".join([ses, folder, fname]))

def none_replace(str_input):
    return str_input

def apply_heuristic(client, heur, acquisition_id, dry_run=False, intended_for=[],
                    metadata_extras={}, subj_replace=None, ses_replace=None, item_num=1):
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
    subj_replace = none_replace if subj_replace is None else subj_replace
    ses_replace = none_replace if ses_replace is None else ses_replace

    acquisition_object = client.get(acquisition_id)
    sess_label = ses_replace(
        client.get(acquisition_object.parents.session).label)
    subj_label = subj_replace(
        client.get(acquisition_object.parents.subject).label)

    files = [f for f in acquisition_object.files if f.type in ftypes]
    bids_keys = ['sub', 'ses', 'folder', 'name']
    ses_fmt = sess_label if sess_label.startswith("ses-") else "ses-" + sess_label

    files.sort(key=operator.itemgetter("name"))
    for fnum, f in enumerate(files):
        bids_vals = template.format(subject=subj_label, session=ses_fmt, item=fnum+1, seqitem=item_num).split("/")
        bids_dict = dict(zip(bids_keys, bids_vals))
        suffix = suffixes[f.type]

        if 'BIDS' not in f.info:
            f.info['BIDS'] = ""
        new_bids = f.info['BIDS']
        if new_bids in ("NA", ""):
            new_bids = add_empty_bids_fields(bids_dict['folder'], bids_dict['name'])
        new_bids['Filename'] = bids_dict['name']+suffix
        new_bids['Folder'] = bids_dict['folder']
        new_bids['Path'] = "/".join([bids_dict['sub'],
                                     bids_dict['ses'],
                                     bids_dict['folder']])
        new_bids['error_message'] = ""
        new_bids['valid'] = True

        infer_params_from_filename(new_bids)

        destination = "\n" + f.name + "\n\t" + new_bids['Filename'] + " -> " + new_bids["Path"] + "/" + new_bids['Filename']
        logger.debug(destination)

        if not dry_run:
            acquisition_object.update_file_info(f.name, {'BIDS': new_bids})

        if intended_for and (f.name.endswith(".nii.gz") or f.name.endswith(".nii")):
            intendeds = [intend.format(subject=subj_label, session=ses_fmt)
                         for intend in intended_for]
            logger.debug("%s IntendedFor: %s", new_bids['Filename'], intendeds)
            if not dry_run:
                acquisition_object.update_file_info(f.name, {'IntendedFor': intendeds})

        if metadata_extras:
            logger.debug("%s metadata: %s", f.name, metadata_extras)
            if not dry_run:
                acquisition_object.update_file_info(f.name, metadata_extras)


def add_empty_bids_fields(folder, fname=None):

    if "fmap" in folder:
        if not fname:
            logger.debug("No filename given, can't set intentions for this fieldmap!")
            IntendedFor = ""
            Modality = ""
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
                    "IntendedFor": "",
                    "Mod": "",
                    "Modality": "",
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
                    "Folder": folder,
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


def infer_params_from_filename(bdict):

    fname = bdict['Filename']

    params = ['Acq', 'Ce', 'Dir', 'Echo', 'Mod', 'Rec', 'Run', 'Task']
    to_fill = {}
    for x in params:
        search = re.search(r'(?<={}-)[A-Za-z0-9]+(?=_)'.format(x.lower()), fname)
        to_fill[x] = search.group() if search is not None else ""

    bdict.update(to_fill)

def confirm_intentions(client, session):

    try:
        acqs = [client.get(s.id) for s in session.acquisitions()]
        acq_files = [f for a in acqs for f in a.files if '.nii' in f.name]
        bids_filenames = [get_nested(f, 'info', 'BIDS', 'Filename') for f in acq_files]
        bids_folders = [get_nested(f, 'info', 'BIDS', 'Folder') for f in acq_files]
        l = list(zip(bids_folders, bids_filenames))
        full_filenames = []
        for x in l:
            if None in x:
                pass
            else:
                full_filenames.append("/".join(x))
        ses_labs = [re.search(r"ses-[a-zA-z0-9]+(?=_)", x).group() for x in full_filenames if x is not None]
        l2 = list(zip(ses_labs, full_filenames))
        paths = []
        for x in l2:
            if not(None in x):
                paths.append("/".join(x))

        for a in acqs:
            for x in a.files:
                if x.type == 'nifti':
                    intendeds = get_nested(x.to_dict(), 'info', 'IntendedFor')
                    if intendeds:
                        if not all([i in paths for i in intendeds]):
                            logger.debug("Ensuring all intentions apply for acquisition %s: %s", a.label, x.name)
                            exists = [i for i in intendeds if i in paths]
                            a.update_file_info(x.name, {'IntendedFor': exists})

    except Exception as e:
        logger.warning("Trouble updating intentions for this session %s", session.label)
        print(e)
        traceback.print_exc()

def confirm_bids_namespace(project_obj, dry_run):

    if get_nested(project_obj, 'info', 'BIDS') is None:

        logger.debug("{} has no BIDS namespace!".format(project_obj.label))

        if not dry_run:

            logger.debug("Adding default BIDS namespace...")

            bids = { 'BIDS': {'Acknowledgements': '',
                'Authors': [],
                'BIDSVersion': '1.0.2',
                'DatasetDOI': '',
                'Funding': '',
                'HowToAcknowledge': '',
                'License': '',
                'Name': project_obj.label,
                'ReferencesAndLinks': [],
                'template': 'project'}
            }

            project_obj.update_info(bids)
            project_obj = project_obj.reload()

    return project_obj
