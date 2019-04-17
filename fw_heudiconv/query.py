import flywheel
import sys
import logging
# from tqdm import tqdm
import re
import warnings
import collections

from heudiconv import utils

CONVERTABLE_TYPES = ("bvec", "bval", "nifti")

log = logging.getLogger(__name__)


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def acquisition_to_heudiconv(acq, context):
    """Create a list of sequence objects for all convertable files in the acquistion."""
    to_convert = []
    # Get the nifti file
    dicoms = [f for f in acq.files if f.type == 'dicom']
    if dicoms:
        dicom = dicoms[0]
        zip_info = acq.get_file_zip_info(dicom.name)
        context['total'] += len(zip_info.members)
    else:
        zip_info = None
    for fileobj in acq.files:
        log.debug('filename: %s', fileobj.name)
        if fileobj.type not in CONVERTABLE_TYPES:
            continue
        info = fileobj.info
        log.debug('uid: %s', info.get("SeriesInstanceUID"))
        to_convert.append(utils.SeqInfo(
            context['total'],
            zip_info.members[0].path if zip_info else None,
            #info.get("SeriesID"),
            acq.id,
            fileobj.name,
            '-',
            '-',
            0,
            0,
            0,
            len(zip_info.members if zip_info else []),
            # We can use the number of files in the
            # Or a corresponding dicom header field
            info.get("RepetitionTime"),
            info.get("EchoTime"),
            info.get("ProtocolName", ""),
            "MOCO" in info.get("ImageType", []),
            "DERIVED" in info.get("ImageType", []),
            info.get("PatientID", context['subject'].code),
            info.get("StudyDescription"),
            info.get("ReferringPhysicianName", ""),
            info.get("SeriesDescription", ""),
            info.get("SequenceName"),
            tuple(info.get("ImageType", [])),
            info.get("AccessionNumber"),
            info.get("PatientAge"),
            info.get("PatientSex"),
            info.get("AcquisitionDate"),
            info.get("SeriesInstanceUID")
        ))
        # We could possible add a context field which would contain flywheel
        # hierarchy information like the subject code and session label
        # or the information fields within them
    return to_convert


def get_seq_info(client, session, context):
    """Returns a SeqInfo OrderedDict for a session

    Args:
        client (Client): The flywheel client
        session (Session): A flywheel session object
        context (dict): The flywheel heirarchy context to pass down

    Returns:
        OrderedDict: The seq info object
    """
    seq_info = collections.OrderedDict()
    context['total'] = 0
    for acquisition in session.acquisitions():
        acquisition = client.get(acquisition.id)
        context['acquisition'] = acquisition

        for info in acquisition_to_heudiconv(acquisition, context):
            log.debug('info: %s', info)
            seq_info[info] = {}  # This would be set to a list of filepaths in
                                 # heudiconv
    log.debug('session=%s', session.label)
    log.debug('Got %s seqinfos', len(seq_info.keys()))
    return seq_info


def query(client, project, subject=None, session=None, grouping=None):
    """Query the flywheel client for a project name
    This function uses the flywheel API to find the first match of a project
    name. The name must be exact so make sure to type it as is on the
    website/GUI.
    Parameters
    ---------
    client
        The flywheel Client class object.
    project
        The name of the project to search for.
    subject
        Subject ID
    session
        Session ID

    Returns
    ---------
    seq_infos
        A list of SeqInfo objects
    """
    project_object = client.projects.find_first('label={0}'.format(project))
    context = {'project': project_object}

    if project_object is None:
        print("Available projects are:\n")
        for p in client.projects():
            print('%s' % (p.label))
        raise ValueError("Could not find \"{0}\" project on Flywheel!".format(project))


    if subject is not None:
        subject = project_object.subjects.find_one('code="{}"'.format(subject))
        sessions = subject.sessions()
    elif session is not None:
        sessions = project_object.sessions.find('label="{}"'.format(session))
    else:
        sessions = project_object.sessions()

    seq_infos = collections.OrderedDict()
    for session in sessions:
        session = client.get(session.id)
        context['subject'] = session.subject
        context['session'] = session
        if grouping is None:
            # All seq infos should be top level if there is no grouping
            for key, val in get_seq_info(client, session, context).items():
                seq_infos[key] = val
        else:
            # For now only supports grouping with session
            seq_infos[session.id] = get_seq_info(client, session, context)

    return seq_infos
