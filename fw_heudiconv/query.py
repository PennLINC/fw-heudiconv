import flywheel
import sys
from tqdm import tqdm
import re
import warnings

CONVERTABLE_TYPES = ("bvec", "bval", "nifti")


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def acquisition_to_heudiconv(client, bson_id):
    """Create a list of sequence objects for all convertable files in the acquistion."""
    acq = client.get(bson_id)
    to_convert = []
    # Get the nifti file
    for fileobj in acq.files:
        if fileobj.type not in CONVERTABLE_TYPES:
            continue
        zip_info = acq.get_file_zip_info(fileobj.name)
        info = fileobj.info
        to_convert.append(DotDict(
            example_dcm_file=zip_info.members[0].path,
            series_id=info.get(""),
            dcm_dir_name=fileobj.name,
            unspecified2='-',
            unspecified3='-',
            dim1
            dim2
            dim3
            dim4=len(zip_info.members), # We can use the number of files in the
                                        # Or a corresponding dicom header field
            TR=info.get("RepetitionTime"),
            protocol_name=info.get("ProtocolName"),
            is_motion_corrected="MOCO" in info.get("ImageType", []),
            is_derived="DERIVED" in info.get("ImageType", []),
            patient_id=info.get("PatientId"),
            study_description=info.get("StudyDescription"),
            referring_physician_name=info.get("ReferringPhysicianName", ""),
            series_description=info.get("SeriesDescription"),
            sequence_name=info.get("SequenceName"),
            image_type=info.get("ImageType"),
            accession_number=info.get("StudyInstanceUID"),
            patient_age=info.get("PatientAge"),
            patient_sex=info.get("PatientSex"),
            date=info.get("AcquisitionDateTime"),
            series_uid=info.get("SeriesInstanceUID")))

class SeqInfo(object):
    """A mock of heudiconv's SeqInfo class.

    Note, this will create seqinfos for all nifti, bval, bvec files,
    even if they're not """
    def __init__(self, client, bson_id):
        self._bson_id = bson_id
        self.acquisitions = []
        for acqnum, acquisition in enumerate(client.get(bson_id).acquisitions()):
            acq = acquisition_to_heudiconv(client, acquisition.id)
            acq.total_files_till_now = acqnum

            self.acquisitions.append(acq)


def query(client, project, subject=None, session=None):
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

    if project_object is None:
        print("Available projects are:\n")
        for p in client.projects():
            print('%s' % (p.label))
        raise ValueError("Could not find \"{0}\" project on Flywheel!".format(project))

    sessions = project_object.sessions()

    if subject is not None:
        sessions = [session for session in sessions
                    if session.subject.label == subject]

    if session is not None:
        sessions = [session for session in sessions
                    if session.label == session]

    return [SeqInfo(client, session.id) for session in sessions]
