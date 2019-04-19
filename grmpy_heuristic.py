import os


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    last_run = len(seqinfo)

    # Create Keys
    t1w = create_key(
       'sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
    t2w = create_key(
       'sub-{subject}/{session}/anat/sub-{subject}_{session}_T2w')
    dwi = create_key(
       'sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-multiband_dwi')

    # Field maps
    b0_phase = create_key(
       'sub-{subject}/{session}/fmap/sub-{subject}_{session}_phasediff')
    b0_mag = create_key(
       'sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude')
    pe_rev = create_key(
        'sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-multiband_dir-j_epi')

    # fmri scans
    rest_mb = create_key(
       'sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold')
    rest_sb = create_key(
       'sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_acq-singleband_bold')
    fracback = create_key(
       'sub-{subject}/{session}/func/sub-{subject}_{session}_task-fracback_acq-singleband_bold')
    face = create_key(
       'sub-{subject}/{session}/func/sub-{subject}_{session}_task-face_acq-singleband_bold')

    # ASL scans
    asl = create_key(
       'sub-{subject}/{session}/asl/sub-{subject}_{session}_asl')
    asl_dicomref = create_key(
       'sub-{subject}/{session}/asl/sub-{subject}_{session}_acq-ref_asl')
    m0 = create_key(
       'sub-{subject}/{session}/asl/sub-{subject}_{session}_m0')
    mean_perf = create_key(
       'sub-{subject}/{session}/asl/sub-{subject}_{session}_mean-perfusion')

    info = {t1w:[], t2w:[], dwi:[], b0_phase:[],
            b0_mag:[], pe_rev:[], rest_mb:[], rest_sb:[],
            fracback:[], asl_dicomref:[], face:[], asl:[],
            m0:[], mean_perf:[]}

    def get_latest_series(key, s):
    #    if len(info[key]) == 0:
        info[key].append(s.series_id)
    #    else:
    #        info[key] = [s.series_id]

    for s in seqinfo:
        protocol = s.protocol_name.lower()
        if "mprage" in protocol:
            get_latest_series(t1w,s)
        elif "t2_sag" in protocol:
            get_latest_series(t2w,s)
        elif "b0map" in protocol and "M" in s.image_type:
            print
            info[b0_mag].append(s.series_id)
        elif "b0map" in protocol and "P" in s.image_type:
            info[b0_phase].append(s.series_id)
        elif "topup_ref" in protocol:
            get_latest_series(pe_rev, s)
        elif "dti_multishell" in protocol and not s.is_derived:
            get_latest_series(dwi, s)

        elif s.series_description.endswith("_ASL"):
            get_latest_series(asl, s)
        elif protocol.startswith("asl_dicomref"):
            get_latest_series(asl_dicomref, s)
        elif s.series_description.endswith("_M0"):
            get_latest_series(m0, s)
        elif s.series_description.endswith("_MeanPerf"):
            get_latest_series(mean_perf, s)

        elif "fracback" in protocol:
            get_latest_series(fracback, s)
        elif "face" in protocol:
            get_latest_series(face,s)
        elif "rest" in protocol:
            if "MB" in s.image_type:
                get_latest_series(rest_mb,s)
            else:
                get_latest_series(rest_sb,s)
        else:
            print("Series not recognized!: ", s.protocol_name, s.dcm_dir_name)
    return info
