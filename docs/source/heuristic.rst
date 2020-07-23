.. _heuristic:

The Heuristic File
====================
BIDS curation of data on Flywheel is implemented through the use of a heuristic file.
Like the name implies, a heuristic is a set of simple and efficient rules that,
for our purposes, will help map DICOM header info to a BIDS-valid filename.

The heuristic's rules are defined in a Python file which is used as input to the
curate command line tool :mod:`fw_heudiconv.cli.curate`. Since it's Python, it's
possible to accomplish a wide variety of logical operations to define these relationships,
but in order to communicate with Flywheel, ``fw-heudiconv`` expects a few
reserved functions and data structures. These functions are documented below.

.. automodule:: fw_heudiconv.example_heuristics.demo

.. autofunction:: fw_heudiconv.example_heuristics.demo.create_key

.. autofunction:: fw_heudiconv.example_heuristics.demo.infotodict

.. autodata:: fw_heudiconv.example_heuristics.demo.MetadataExtras

.. autodata:: fw_heudiconv.example_heuristics.demo.IntendedFor

.. autofunction:: fw_heudiconv.example_heuristics.demo.ReplaceSubject

.. autofunction:: fw_heudiconv.example_heuristics.demo.ReplaceSession

.. autofunction:: fw_heudiconv.example_heuristics.demo.AttachToSession

.. autofunction:: fw_heudiconv.example_heuristics.demo.AttachToProject

A Real Example
---------------
In all, a heuristic file could look like this:

.. code-block:: python

    import os

    def create_key(template, outtype=('nii.gz',), annotation_classes=None):
        if template is None or not template:
            raise ValueError('Template must be a valid format string')
        return template, outtype, annotation_classes

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
       'sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude{item}')
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
       'sub-{subject}/{session}/perf/sub-{subject}_{session}_asl')
    asl_dicomref = create_key(
       'sub-{subject}/{session}/perf/sub-{subject}_{session}_acq-ref_asl')
    m0 = create_key(
       'sub-{subject}/{session}/perf/sub-{subject}_{session}_m0')
    mean_perf = create_key(
       'sub-{subject}/{session}/perf/sub-{subject}_{session}_mean-perfusion')


    def infotodict(seqinfo):

        last_run = len(seqinfo)

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

            elif s.patient_id in s.dcm_dir_name:
                get_latest_series(asl, s)

            else:
                print("Series not recognized!: ", s.protocol_name, s.dcm_dir_name)
        return info

    MetadataExtras = {
        b0_phase: {
            "EchoTime1": 0.00412,
            "EchoTime2": 0.00658
        },
        asl: {
            "PulseSequenceType": "3D_SPRIAL",
            "PulseSequenceDetails" : "WIP" ,
            "LabelingType": "PCASL",
            "LabelingDuration": 1.8,
            "PostLabelingDelay": 1.8,
            "BackgroundSuppression": "Yes",
            "M0":10,
            "LabelingSlabLocation":"X",
            "LabelingOrientation":"",
            "LabelingDistance":2,
            "AverageLabelingGradient": 34,
            "SliceSelectiveLabelingGradient":45,
            "AverageB1LabelingPulses": 0,
            "LabelingSlabThickness":2,
            "AcquisitionDuration":123,
            "BackgroundSuppressionLength":2,
            "BackgroundSuppressionPulseTime":2,
            "VascularCrushingVenc": 2,
            "PulseDuration": 1.8,
            "InterPulseSpacing":4,
            "PCASLType":"balanced",
            "PASLType": "",
            "LookLocker":"True",
            "LabelingEfficiency":0.72,
            "BolusCutOffFlag":"False",
            "BolusCutOffTimingSequence":"False",
            "BolusCutOffDelayTime":0,
            "BolusCutOffTechnique":"False"
        }
    }

    IntendedFor = {
        b0_phase: [
            '{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold.nii.gz',
            '{session}/func/sub-{subject}_{session}_task-rest_acq-singleband_bold.nii.gz',
            '{session}/func/sub-{subject}_{session}_task-fracback_acq-singleband_bold.nii.gz',
            '{session}/func/sub-{subject}_{session}_task-face_acq-singleband_bold.nii.gz'
        ],
        b0_mag: [],
        pe_rev: [
            '{session}/dwi/sub-{subject}_{session}_acq-multiband_dwi.nii.gz',
        ]
    }

    def ReplaceSubject(label):
        return label.lstrip("0")


    def ReplaceSession(label):
        return label.lstrip("0")


    def AttachToSession():

        # example: uploading a json file
        import json

        adict = {
            "id": "04",
            "name": "foo",
            "scan": "blah"
        }

        json_object = json.dumps(adict, indent = 4) # json.dumps() returns a string!

        attachment1 = {
            'name': 'jsonexample.json',
            'data': json_object,
            'type': 'application/json'
        }

        return attachment1


    def AttachToProject():

        # example: uploading a single CHANGES file

        attachment1 = {
            'name': 'CHANGES',
            'data': 'This is a CHANGES file!',
            'type': 'text/plain'
        }

        return attachment1
