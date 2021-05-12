import logging
import collections
import os
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    from nibabel.nicom.dicomwrappers import wrapper_from_data

from heudiconv import utils

CONVERTABLE_TYPES = ("bvec", "bval", "nifti")

log = logging.getLogger(__name__)


def acquisition_to_heudiconv(client, acq, context):
    """Create a list of sequence objects for all convertable files in the acquistion."""
    to_convert = []
    # Get the nifti file
    dicoms = [f for f in acq.files if f.type == 'dicom']
    if dicoms:
        dicom = dicoms[0]
        try:
            zip_info = acq.get_file_zip_info(dicom.name)
            context['total'] += len(zip_info.members)
            dcm_info = dicom.info

        except:
            except_subj = client.get(acq.parents.subject)
            except_sess = client.get(acq.parents.session)

            log.debug('Dicom could not be processed:\n\t%s\n\tSubject Label: %s\n\tSession Label: %s'.format(dicom.name, except_subj.label, except_sess.label))
            zip_info = None
            dcm_info = {}

    else:
        zip_info = None
        dcm_info = {}
    # Make it a nicom wrapper to handle all sorts of different dicom styles
    mw = wrapper_from_data(dcm_info)
    num_dicoms = len(zip_info.members) if zip_info else -1
    image_shape = mw.image_shape
    if image_shape is None:
        image_shape = (-1, -1, -1, -1)
    else:
        image_shape = mw.image_shape + (num_dicoms,)
        while len(image_shape) < 4:
            image_shape = image_shape + (-1,)

    for fileobj in acq.files:
        log.debug('filename: %s', fileobj.name)
        if fileobj.type not in CONVERTABLE_TYPES:
            continue
        info = fileobj.info

        # Make it a nicom wrapper to handle all sorts of different dicom styles
        mw = wrapper_from_data(info)

        log.debug('uid: %s', info.get("SeriesInstanceUID"))
        to_convert.append(utils.SeqInfo(
            context['total'],
            zip_info.members[0].path if zip_info else None,
            acq.id,
            fileobj.name,
            '-',
            '-',
            image_shape[0],
            image_shape[1],
            image_shape[2],
            image_shape[3],
            # We can use the number of files in the
            # Or a corresponding dicom header field
            info.get("RepetitionTime"),
            info.get("EchoTime"),
            info.get("ProtocolName", ""),
            "MOCO" in info.get("ImageType", []),
            "DERIVED" in info.get("ImageType", []),
            context['subject'].label,
            info.get("StudyDescription"),
            info.get("ReferringPhysicianName", ""),
            info.get("SeriesDescription", ""),
            info.get("SequenceName"),
            tuple(info.get("ImageType", [])),
            info.get("AccessionNumber"),
            info.get("PatientAge"),
            info.get("PatientSex"),
            info.get("AcquisitionDateTime"),
            info.get("SeriesInstanceUID")
        ))
        # We could possible add a context field which would contain flywheel
        # hierarchy information like the subject code and session label
        # or the information fields within them
    return to_convert


def session_to_seq_info(client, session, context):
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
    acquisitions = session.acquisitions()
    #sorted_acquisitions = sorted(acquisitions, key=lambda x: x.timestamp or '')
    for acquisition in acquisitions:
        acquisition = client.get(acquisition.id)
        context['acquisition'] = acquisition

        for info in acquisition_to_heudiconv(client, acquisition, context):
            log.debug('info: %s', info)
            seq_info[info] = {}  # This would be set to a list of filepaths in heudiconv
    log.debug('session=%s', session.label)
    log.debug('Got %s seqinfos', len(seq_info.keys()))
    return seq_info


def get_sessions(client, project, subject=None, session=None):
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
    context = {'project': project_object}   # what is this?

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

    return sessions


def get_seq_info(client, project, sessions, grouping=None):

    project_object = client.projects.find_first('label={0}'.format(project))
    context = {'project': project_object}

    seq_infos = collections.OrderedDict()
    for session in sessions:
        session = client.get(session.id)
        context['subject'] = session.subject
        context['session'] = session
        if grouping is None:
            # All seq infos should be top level if there is no grouping
            for key, val in session_to_seq_info(client, session, context).items():
                seq_infos[key] = val
        else:
            # For now only supports grouping with session
            seq_infos[session.id] = session_to_seq_info(client, session, context)

    return seq_infos


def print_directory_tree(startpath):
    '''
    https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
    '''
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))
