import flywheel

seqinfo_fields = [
    'total_files_till_now',  # 0
    'example_dcm_file',      # 1
    'series_id',             # 2
    'dcm_dir_name',          # 3
    'unspecified2',          # 4
    'unspecified3',          # 5
    'dim1', 'dim2', 'dim3', 'dim4', # 6, 7, 8, 9
    'TR', 'TE',              # 10, 11
    'protocol_name',         # 12
    'is_motion_corrected',   # 13
    'is_derived',            # 14
    'patient_id',            # 15
    'study_description',     # 16
    'referring_physician_name', # 17
    'series_description',    # 18
    'sequence_name',         # 19
    'image_type',            # 20
    'accession_number',      # 21
    'patient_age',           # 22
    'patient_sex',           # 23
    'date',                  # 24
    'series_uid'             # 25
 ]

SeqInfo = namedtuple('SeqInfo', seqinfo_fields)


def seqinfo_from_acquisition(acquisition):
    """Using a flywheel acquisition object and the files in it, generates a
    "SeqInfo" object that is passed to the heuristics

    NOTE: The acquisition object must be a full object, not one returned from
    a list or finder, as it requires the info fields of itself and its files

    Args:
        acquisition (Acquisition): A flywheel acquisition object

    Returns:
        SeqInfo: A named tuple containing the field defined in swqinfo_fields
        None: acquisition doesn't have a dicom
    """
    dicoms = [ f for f in acquisition.files if f.type == 'dicom' ]
    if dicoms:
        dicom = dicoms[0]
    else:
        return None


    # Grab a single image for the example
    zip_info = acquisition.get_file_zip_info(dicom.name)
    example_dcm_file = zip_info.members[0].path

    total = len(zip_info.members)

    series_id = dicom.info.get('SeriesId')
    dcm_dir_name = dicom.name
    # # Not sure what the first 3 dimension refer to, I didn't see
    # sizes = len(zip_info.members)
    TR = float(dicom.info.get('RepititionTime', -1000)/1000.
    TE = float(dicom.info.get('EchoTime', -1000)/1000.
    protocol_name = dicom.info.get('ProtocolName')

    image_type = dicom.info.get('ImageType', [])
    motion_corrected = 'MOCO' in image_type
    derived = 'derived' in [ it.lower() for it in image_type ]
    patient_id = dicom.info.get('PatientID')
    study_description = dicom.info.get('StudyDescription')
    refphys = str(dicom.info.get('ReferringPhysicianName', ''))
    series_description = dicom.info.get('SeriesDescription')
    sequence_name = dicom.info.get('SequenceName')
    accession_number = dicom.info.get('AccessionNumber')
    patient_age = dicom.info.get('PatientAge')
    patient_sex = dicom.info.get('PatientSex')
    acquisition_date = dicom.info.get('AcquisitionDate')
    series_instance_uid = dicom.info.get('SeriesInstanceUID')

    seqinfo = SeqInfo(
        total,
        example_dcm_file,
        series_id,
        dcm_dir_name,
        '-', '-',
        sizes[0], sizes[1], sizes[2], sizes[3],
        TR, TE,
        protocol_name,
        motion_corrected,
        derived,
        patient_id,
        StudyDescription,
        refphys,
        series_description,
        sequence_name,
        image_type,
        accession_number,
        patient_age,
        patient_sex,
        acquisition_date,
        series_instance_uid
    )

    # # Not sure what is going on here
    # if per_studyUID:
    #     if studyUID not in seqinfo:
    #         seqinfo[studyUID] = OrderedDict()
    #     seqinfo[studyUID][info] = series_files
    # elif per_accession_number:
    #     if accession_number not in seqinfo:
    #         seqinfo[accession_number] = OrderedDict()
    #     seqinfo[accession_number][info] = series_files
    # else:
    #     seqinfo[info] = series_files

