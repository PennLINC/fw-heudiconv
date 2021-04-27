.. _stepbystep:

Step-By-Step Guide
====================
Let's walk through an example of how to curate some simple data on Flywheel. For
this tutorial, you will at the very least need access to Flywheel and a text editor.

Step 1: Understanding Your Dataset in the Context of BIDS
---------------------------------------------------------

Before you can curate the dataset into BIDS, it's important to be able to
predict how your dataset should look in BIDS. If you don't know what BIDS is,
check the official `readthedocs <https://bids-specification.readthedocs.io/en/stable/>`_.

Our goal here will be to map DICOMs to NIfTIs named correctly in BIDS,
including the directory structure, correct metadata sidecars, and fieldmap files:

.. image:: dicom-reorganization-transparent-white_1000x477.png
   :width: 600

To start, we need to figure out what we can use to create this "mapping". In
``fw-heudiconv`` curation, this mapping is called a heuristic, and we'll use
the DICOMs' header information to create rules for this mapping. To extract this
information, we will use ``fw-heudiconv-tabulate`` to generate a `seqinfo table`.

``fw-heudiconv-tabulate``
-------------------------

In the Flywheel GUI, from within a project, select the "Analysis" tab:

.. image:: project_analysis_view.png
   :width: 1200

Click the "Run Analysis Gear" button, which will drop down the analysis box. In
this box, select ``Flywheel HeuDiConv`` as the gear to run the analysis.

.. image:: project_gear_view.png
   :width: 1200

From here, click the "Configuration" tab (there are no inputs required at
this stage). This will allow you to set the configuration for the gear. Under
"Action", select "Tabulate", and make sure to *uncheck* ``dry_run``. When ready,
hit "Run Gear"!

The same can be accomplished at the command line, with this command:

.. code-block:: python

    fw-heudiconv-tabulate --project FlywheelTools_TestData --path MY/OUTPUT/DIRECTORY/


The Output
^^^^^^^^^^

You should now see an analysis object appear in the GUI. This analysis object is
associated with the project, since we started it at the project level. If a blue
gear is spinning, the gear is still running (this can include virtual machine
initialization and shut down time); a red X means it failed, but a green check
means success! You should be able to check the "Gear Logs" in the analysis object
to read through ``stdout`` (all the commands and outputs) as the gear ran.

.. image:: tabulate_log.png
   :width: 1200

In the Results section of the analysis, Flywheel zips all the data it was
instructed to save as outputs -- in this case, the result of our tabulation.
Download this file and unzip it, afterwhich you can open it in your table viewer
or text editor of choice.

.. image:: tabulate_table.png
   :width: 1200

Next, we're going to use this table to curate one of the subjects. Fortunately,
in the table viewer, we can use a filter to only show data from one subject.
Here, we pick subject 019459 using the ``patient_id`` column.

Developing a Simple Heuristic
-----------------------------

To start, open up any text editor, such as Notepad or TextEdit. We're going to
start by curating the anatomical T1w image, whose DICOM is highlighted here:

.. image:: t1w_seqinfo.png
   :width: 1200

In-depth knowledge of these functions is not necessary for this tutorial, but
see :ref:`heuristic` if you want to understand each of them in earnest. First,
copy and paste the ``create_key()`` function into a new file in your text editor:

.. code-block:: python

    def create_key(template, outtype=('nii.gz',), annotation_classes=None):
        if template is None or not template:
            raise ValueError('Template must be a valid format string')
        return template, outtype, annotation_classes

Next, use this function to create a BIDS name for the T1w NIfTI you want:

.. code-block:: python

    def create_key(template, outtype=('nii.gz',), annotation_classes=None):
        if template is None or not template:
            raise ValueError('Template must be a valid format string')
        return template, outtype, annotation_classes

    # Create Keys
    t1w = create_key(
       'sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T1w')

When ``fw-heudiconv`` runs this heuristic, there will exist a variable called
``t1w``, and it will have the string specifying the BIDS file name and path
for a T1w (relative to the BIDS root). The next step is making sure that the
DICOM we selected will be assigned to this variable. The next function we will
use to do that is the ``infotodict`` function:

.. code-block:: python

    def infotodict(seqinfo):

        info = {
          t1w: []
        }

        for s in seqinfo:
            if "MPRAGE" in s.series_description:
                info[t1w].append(s.series_id)

        return info

After the function is defined with ``def``, we create the ``info`` object -- a
Python dictionary with one key, ``t1w``, and an empty list. Our goal is to
populate this dictionary with the list of DICOMs who belong to the ``t1w`` key.

The input to this function, ``seqinfo``, is `each row from your seqinfo table`.
So looping over the object ``seqinfo`` gives you access to each row of your table,
where the variables in the table are accessed using Python.

In our example above, we access ``series_description`` and check if it contains the
string ``MPRAGE``. We know our T1w is the only one that has this string:

.. image:: t1w_highlighted.png
   :width: 1200

So we `append` the ``series_id`` value of that row (the unique identifier of
the DICOM) to the list of files that should be named this way -- the ``t1w`` key.
The heuristic at this point should look like this:

.. code-block:: python

    def create_key(template, outtype=('nii.gz',), annotation_classes=None):
        if template is None or not template:
            raise ValueError('Template must be a valid format string')
        return template, outtype, annotation_classes

    # Create Keys
    t1w = create_key(
       'sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T1w')

    # loop over the seqinfo table
    def infotodict(seqinfo):

        # the dictionary of keys and list of files they correspond to
        info = {
          t1w: []
        }

        # loop over each row of your seqinfo table
        for s in seqinfo:

            # if the series description contains "MPRAGE",
            # add the DICOM identifier to the dictionary

            if "MPRAGE" in s.series_description:
                info[t1w].append(s.series_id)

      return info

Save this file as ``my_test_heuristic.py`` -- we're going to use it in the next
section to curate the T1w image!



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
