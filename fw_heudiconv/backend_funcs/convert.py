import logging
import re
import pdb
import operator
import pprint
import mimetypes
import flywheel
import json
import pandas as pd
from os import path
from pathvalidate import is_valid_filename
from pathlib import Path
from fw_heudiconv.cli.export import get_nested

logger = logging.getLogger('fw-heudiconv-curator')


def build_intention_path(f):
    """Builds a string of the path to the file w.r.t. subject dir
    """
    fname = f.info["BIDS"]["Filename"]
    folder = f.info["BIDS"]["Folder"]
    ses = fname.split("_")[1]
    return("/".join([ses, folder, fname]))


def none_replace(str_input):
    return str_input


def force_template_format(str_input):

    # if we get a reproin heuristic, the str format is:
    #
    # {bids_subject_session_dir}/anat/{bids_subject_session_prefix}_scout
    #
    # here we replace the {} with the sub-sess format fw-heudiconv uses

    str_input = re.sub("{bids_subject_session_dir}", "sub-{subject}/ses-{session}", str_input)
    str_input = re.sub("{bids_subject_session_prefix}", "sub-{subject}_ses-{session}", str_input)

    # next, we remove extra sub-sub or ses-ses
    str_input = re.sub("(?<!ses-){session}", "ses-{session}", str_input)
    str_input = re.sub("(?<!sub-){subject}", "sub-{subject}", str_input)

    return(str_input)


def force_label_format(str_input):

    str_input = re.sub("ses-", "", str_input)
    str_input = re.sub("sub-", "", str_input)

    return(str_input)


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
    template = force_template_format(template)

    subj_replace = none_replace if subj_replace is None else subj_replace
    ses_replace = none_replace if ses_replace is None else ses_replace

    acquisition_object = client.get(acquisition_id)
    subj_label = subj_replace(force_label_format(client.get(acquisition_object.parents.subject).label))
    sess_label = ses_replace(force_label_format(client.get(acquisition_object.parents.session).label))

    files = [f for f in acquisition_object.files if f.type in ftypes]
    bids_keys = ['sub', 'ses', 'folder', 'name']

    files.sort(key=operator.itemgetter("name"))
    for fnum, f in enumerate(files):
        bids_vals = template.format(subject=subj_label, session=sess_label, item=fnum+1, seqitem=item_num).split("/")
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

        destination = "\n" + f.name + "\n\t" + new_bids['Filename'] + " -> " \
            + new_bids["Path"] + "/" + new_bids['Filename']
        logger.debug(destination)

        if not dry_run:
            acquisition_object.update_file_info(f.name, {'BIDS': new_bids})
            acquisition_object = client.get(acquisition_id) # Refresh the acquisition object

        if intended_for and (f.name.endswith(".nii.gz") or f.name.endswith(".nii")):

            intendeds = [force_template_format(intend)
                         for intend in intended_for]
            intendeds = [intend.format(subject=subj_label, session=sess_label)
                         for intend in intendeds]

            logger.debug("%s IntendedFor: %s", pprint.pformat(new_bids['Filename']),
                         pprint.pformat(intendeds))
            if not dry_run:
                acquisition_object.update_file_info(f.name, {'IntendedFor': intendeds})
                acquisition_object = client.get(acquisition_id)
                # Check that it was applied
                file_info = acquisition_object.get_file(f.name)
                assert file_info['info']['IntendedFor'] == intendeds
                logger.debug("Applied!")

        if metadata_extras:
            logger.debug("%s metadata: %s", f.name, metadata_extras)
            if not dry_run:
                old_metadata = get_metadata_from_acq(client, acquisition_object, f.name)
                new_metadata = old_metadata.copy()
                new_metadata.update(metadata_extras)
                acquisition_object.update_file_info(f.name, new_metadata)


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


def confirm_intentions(client, session, dry_run=False):
    """Ensure that files in "IntededFor" will ultimately exist in the BIDS directory.
    """
    try:
        acqs = [client.get(s.id) for s in session.acquisitions()]
        acq_files = [f for a in acqs for f in a.files if '.nii' in f.name]
        bids_filenames = [get_nested(f, 'info', 'BIDS', 'Filename') for f in acq_files]
        bids_paths = [get_nested(f, 'info', 'BIDS', 'Path') for f in acq_files]
        full_filenames = []
        for folder, filename in zip(bids_paths, bids_filenames):
            if None in (folder, filename) or '' in (filename, folder):
                continue
            full_filenames.append(folder + "/" + filename)

        bids_files = [re.sub("sub-[a-zA-z0-9]+/", "", x) for x in full_filenames]

        # Go through all the acquisitions in the session
        for acq in acqs:
            for acq_file in acq.files:
                if not acq_file.type == 'nifti':
                    continue
                intendeds = get_nested(acq_file.to_dict(), 'info', 'IntendedFor')
                if not intendeds:
                    continue
                # If there are "IntendedFor" values, check that they will exist
                logger.debug(
                    "Ensuring all intentions apply for acquisition %s: %s",
                    acq.label, acq_file.name)

                ok_intentions = []
                bad_intentions = []
                for intendedfor in intendeds:
                    if intendedfor in bids_files:
                        ok_intentions.append(intendedfor)
                    else:
                        bad_intentions.append(intendedfor)

                if bad_intentions:
                    logger.warning(
                        "IntendedFor values do not point to a BIDS file: %s",
                        bad_intentions)
                    # pdb.set_trace()
                if not dry_run:
                    acq.update_file_info(acq_file.name,
                                         {'IntendedFor': ok_intentions})

    except Exception as e:
        logger.warning("Trouble updating intentions for this session %s", session.label)
        logger.warning(e)


def confirm_bids_namespace(project_obj, dry_run):

    bids_info = get_nested(project_obj, 'info', 'BIDS')
    if bids_info in (None, ''):

        logger.debug("{} has no BIDS namespace!".format(project_obj.label))

        if not dry_run:

            logger.debug("Adding default BIDS namespace...")

            bids = {
                'BIDS': {'Acknowledgements': '',
                'Authors': [],
                'BIDSVersion': '1.6.0',
                'DatasetDOI': '',
                'Funding': [],
                'HowToAcknowledge': '',
                'License': '',
                'Name': project_obj.label,
                'ReferencesAndLinks': [],
                'template': 'project'}
            }

            project_obj.update_info(bids)
            project_obj = project_obj.reload()

    return project_obj


def verify_attachment(name, data, dtype='text/tab-separated-values'):

    types = mimetypes.types_map

    # check for extension
    # if found, check its dtype matches
    ext = path.splitext(name)[1]
    valid_fname = is_valid_filename(name)

    if ext:

        output_dtype = types.get(ext, None)
        if dtype == output_dtype:
            valid_dtype = True
        else:
            valid_dtype = False
    else:
        # no extension, just check dtype
        valid_dtype = dtype in list(mimetypes.types_map.values())

    valid_data = isinstance(data, str)

    return valid_fname, valid_data, valid_dtype


def upload_attachment(
    client, target_object, level, attachment_dict,
    subject_rename=None, session_rename=None,
    folders=['anat', 'dwi', 'func', 'fmap', 'perf'],
    dry_run=True
        ):
    '''processes and uploads the attachment
    '''

    bids = {
        "Filename": None,
        "Folder": None,
        "Path": None
        }

    if level == 'project':
        bids.update({
            "Filename": attachment_dict['name'],
            "Path": '.'
            })
    else:

        # manipulate sub and ses labels
        subj_replace = none_replace if subject_rename is None else subject_rename
        subj_label = subj_replace(force_label_format(target_object.subject.label))

        ses_replace = none_replace if session_rename is None else session_rename
        sess_label = ses_replace(force_label_format(target_object.label))

        attachment_dict['name'] = force_template_format(attachment_dict['name'])
        attachment_dict['name'] = attachment_dict['name'].format(subject=subj_label, session=sess_label)

        # get the dir/folder/path
        dirs = Path(attachment_dict['name']).parts
        folder = [x for x in dirs if x in folders]
        if not folder:
            folder = None
        else:
            folder = folder[0]

        path = str(Path(attachment_dict['name']).parent)

        # get filename
        attachment_dict['name'] = str(Path(attachment_dict['name']).name)

        # get BIDS ready
        bids.update({
            "Filename": str(Path(attachment_dict['name']).name),
            "Folder": folder,
            "Path": path
            })
    logger.debug(
        "Attachment details:\n\tFilename: {}\n\tData: {}\n\tMIMEType: {}".format(
            attachment_dict['name'], attachment_dict['data'], attachment_dict['type']
        )
    )
    logger.debug(
        "Updating BIDS: \n\t{}".format(bids)
    )

    verify_name, verify_data, verify_type = verify_attachment(
        attachment_dict['name'], attachment_dict['data'], attachment_dict['type']
        )

    if not all([verify_name, verify_data, verify_type]):

        logger.warning("Attachments may not be valid for upload!")
        logger.debug(
            "\tFilename valid: {}\n\tData valid: {}\n\tMIMEType valid: {}".format(
                verify_name, verify_data, verify_type
            )
        )

    if not dry_run:
        file_spec = flywheel.FileSpec(
            attachment_dict['name'], attachment_dict['data'], attachment_dict['type']
            )
        target_object.upload_file(file_spec)
        target_object = target_object.reload()
        target_object.update_file_info(attachment_dict['name'], {'BIDS': bids})
        logger.info("Attachment uploaded!")

def parse_validator(path):

    with open(path, 'r') as read_file:
        data = json.load(read_file)

    issues = data['issues']

    def parse_issue(issue_dict):

        return_dict = {}
        return_dict['files'] = [get_nested(x, 'file', 'relativePath') for x in issue_dict.get('files', '')]
        return_dict['type'] = issue_dict.get('key' '')
        return_dict['severity'] = issue_dict.get('severity', '')
        return_dict['description'] = issue_dict.get('reason', '')
        return_dict['code'] = issue_dict.get('code', '')
        return_dict['url'] = issue_dict.get('helpUrl', '')

        return(return_dict)

    df = pd.DataFrame()

    for warn in issues['warnings']:

        parsed = parse_issue(warn)
        parsed = pd.DataFrame(parsed)
        df = df.append(parsed, ignore_index=True)

    for err in issues['errors']:

        parsed = parse_issue(err)
        parsed = pd.DataFrame(parsed)
        df = df.append(parsed, ignore_index=True)

    return df

def get_metadata_from_acq(client, acq, filename):

    acq = client.get(acq.id)

    target_file = [f for f in acq.files if f.name == filename][0]

    return target_file['info']
