'''
How ``fw-heudiconv`` Uses a Heuristic
=====================================

Once ``fw-heudiconv`` has parsed arguments and filtered out the target sessions
to curate, ``fw-heudiconv`` then gathers all of the DICOM header information in
a session's acquisitions. In the program, we call these objects ``seqinfo`` objects.
The program loops over each of these ``seqinfo`` objects and tests each
one to see if the heuristic has defined a BIDS filename for a ``seqinfo`` of this
type. If so, it adds a reference to this ``seqinfo`` to a special internal list.
At the end of the checks, ``fw-heudiconv`` goes through the list of references,
adding BIDS metadata to each of the NIfTIs the references point to.

To accomplish all of this, you need to craft a proper heuristic. We cover each of
the functions next.

Heuristic Functions
===================
This heuristic demonstrates all of the functionalities available in fw-heudiconv
data curation.

Mandatory functions
-------------------
There are two mandatory functions that are expected in a heuristic. The first is
the :func:`create_key` function. This function allows the heuristic to define BIDS-
valid filenames for each scan type and category you expect to find. Once defined,
you can then assign keys to variables to be used in the next mandatory function.

The next mandatory function is :func:`infotodict`. This function does the heavy lifting —
it loops over the ``seqinfo`` objects, and uses boolean logic in each to decide if
it is going to be assigned to a BIDS key.

Optional variables
------------------
There are optional variables you can use to hardcode metadata into the BIDS sidecar
or define fieldmap intentions (:data:`MetadataExtras` and :data:`IntendedFor`).

``Replace*`` functions
-----------------------
There are optional functions that assist with Flywheel-specific data
manipulation. The first of these is the :func:`ReplaceSubject` and :func:`ReplaceSession`
functions, which can be used to manipulate the label of a Flywheel object before
it is inserted into a BIDS filename (for example, to remove leading zeroes).
These functions are expected to have a string as input (the Flywheel label) and
the return object to be a string of your making. These functions *don't* affect
the source data objects on Flywheel, only the metadata BIDS fields.

``Attach*`` functions
----------------------
Then there are the :func:`AttachToProject` and :func:`AttachToSession` functions, which
are used to dynamically generate and upload BIDS metadata files, like participant
or event files. We've found these functions useful for generating and uploading
ASL context files, but can be used for any dynamic file attachment purpose,
so long as the data can be parsed into a raw text string.
'''

import os


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    '''
    Create a BIDS key

    Use this function to create a BIDS key with keywords to be populated at runtime.
    Keys **must** be BIDS valid and have the full BIDS path; the file extension is
    **not** required. Available keywords are as follows:

    =========  ===============================================
    {subject}  The subject label
    {session}  The session label
    {item}     An iterator to be used *within* an acquisition
    =========  ===============================================

    Example:

    >>> t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
    >>> t1w
    ('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w', ('nii.gz',), None)
    >>> rest_mb = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold')
    >>> rest_mb
    ('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold', ('nii.gz',), None)
    '''
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

def infotodict(seqinfo):
    """Heuristic evaluator for mapping seqinfos to BIDS filenames

    A function for defining the boolean logic that determines how to map
    a seqinfo to a key made with :func:`create_key`. The ``seqinfo`` object has
    a number of attributes that can be tested in boolean logic; when a match is found,
    the ``series_id`` attribute is added to a list that tracks the matches.

    All usable attributes are listed as columns in the output of the tabulate tool
    (for example, all DICOMs have a ``series_description``, which shows up as a column in the output of
    ``fw-heudiconv-tabulate``; you can access this attribute using ``s.series_description``).

    The return object **must** be a dictionary where each *key* is a ``key`` variable already
    earlier defined in the namespace, and the corresponding *value* is a list of ``series_id``.

    We find that the easiest way to accomplish this (and debug iteratively) is
    with the use of a for-loop.

    :param seqinfo: a ``fw-heudiconv`` seqinfo object, enumerating DICOM metadata as attributes
    :returns: dictionary -- a dictionary of keys and a list of seqinfo series IDs that match the key

    Example:

    >>> t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
    >>> t1w
    ('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w', ('nii.gz',), None)
    >>> rest_mb = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold')
    >>> rest_mb
    ('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold', ('nii.gz',), None)

    >>> def infotodict(seqinfo):
    ...     info = {t1w:[], rest_mb:[]}
    ...     for s in seqinfo:
    ...         protocol = s.protocol_name.lower()
    ...         if "mprage" in protocol:
    ...             info[t1w].append(s.series_id)
    ...         elif "rest" in protocol:
    ...             info[rest_mb].append(s.series_id)
    ...         else:
    ...             print('Series {} not found!'.format(protocol_name))
    ...     return info

    """
    return


MetadataExtras = {}
'''Special variable defining metadata to hardcodeinto the BIDS sidecar.

Use this variable to define metadata that you want to hardcode into the BIDS
sidecar. For example, we could use this to hardcode the EchoTime for phase fieldmaps,
or for use in ASL, we can use this to hardcode metadata that sometimes
isn't extracted by ``dcm2niix``.

This variable **must** be a dictionary, where the *key* is a ``key`` variable already
earlier defined in the namespace, and the *value* is itself a dictionary of
metadata.

Example (we've already defined keys ``b0_phase`` and ``asl`` with ``create_key``):

>>> MetadataExtras = {
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
'''

IntendedFor = {}
'''Special variable mapping fieldmaps to scans.

Use this variable to define which files your fieldmaps are intended to correct
for. You do this by using the fieldmap keys defined with ``create_key``, and a
list of filenames where the keywords ``{subject}``, ``{session}`` and others
are used for ambiguity. ``fw-heudiconv`` will check for each file and try to map
IntendedFor's appropriately.

This variable **must** be a dictionary, where the *key* is a ``key`` variable already
earlier defined in the namespace, and the *value* is a list of filename templates.

Example (we've already defined ``b0_phase``, ``b0_phase``, ``pe_rev`` with ``create_key``):

>>> IntendedFor = {
    b0_phase: [
        '{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold.nii.gz',
        '{session}/func/sub-{subject}_{session}_task-rest_acq-singleband_bold.nii.gz',
        '{session}/func/sub-{subject}_{session}_task-fracback_acq-singleband_bold.nii.gz',
        '{session}/func/sub-{subject}_{session}_task-face_acq-singleband_bold.nii.gz'
    ],
    b0_mag: [
        '{session}/func/sub-{subject}_{session}_task-rest_acq-multiband_bold.nii.gz',
        '{session}/func/sub-{subject}_{session}_task-rest_acq-singleband_bold.nii.gz',
        '{session}/func/sub-{subject}_{session}_task-fracback_acq-singleband_bold.nii.gz',
        '{session}/func/sub-{subject}_{session}_task-face_acq-singleband_bold.nii.gz'
    ],
    pe_rev: [
        '{session}/dwi/sub-{subject}_{session}_acq-multiband_dwi.nii.gz',
    ]
}
'''


def ReplaceSubject(label):
    '''
    Manipulate the BIDS subject label

    Use this function to define how to manipulate a subject's label on Flywheel
    into a BIDS valid <subject> value

    :param label: the Flywheel subject label
    :type label: string
    :returns: string -- the manipulated string label

    Example -- stripping leading zeroes from a subject label:

    >>> def ReplaceSubject(label):
    ...     return label.lstrip('0')
    >>> ReplaceSubject('01234')
    '1234'
    '''
    return label


def ReplaceSession(label):
    '''
    Manipulate the BIDS session label

    Use this function to define how to manipulate a session's label on Flywheel
    into a BIDS valid <session> value

    :param label: the Flywheel session label
    :type label: string
    :returns: string -- the manipulated string label

    Example -- enforcing all sessions are labelled 01:

    >>> def ReplaceSession(label):
    ...     return '01'
    >>> ReplaceSession('SomeSession')
    '01'
    '''
    return label


def AttachToSession():
    '''
    Attach BIDS data files to a project at the session level

    Use this function to dynamically generate files and upload them to the BIDS
    project at the session level. The filename **must** be BIDS valid. Examples
    include the ``events.tsv`` file or the ``aslcontext.tsv`` file.

    This function takes no input but **must** return a dictionary (or list of dictionaries) with three
    parts:

    1. ``name``: the BIDS filename, with optional keywords for formatting (e.g. ``{subject}``).
    2. ``data``: the data to upload, which **must** be in literal string format.
    3. ``type``: the file MIMEType; see `Link here <https://www.freeformatter.com/mime-types-list.html>`_ for available types.

    :returns: dictionary -- the dictionary containing BIDS data

    Example -- creating an ASL context file from scratch to attach to each session:

    >>> def AttachToSession():
    ...     attachment1 = {
    ...         'name': '{subject}/{session}/perf/{subject}_{session}_aslcontext.tsv',
    ...         'data': '\\n'.join(['Control', 'Label', 'Control', 'Label']),
    ...         'type': 'text/tab-separated-values'
    ...     }
    ...     return attachment1

    >>> AttachToSession()
    {'name': '{subject}/{session}/perf/{subject}_{session}_aslcontext.tsv', 'data': 'Control\\nLabel\\nControl\\nLabel', 'type': 'text/tab-separated-values'}
    '''
    return


def AttachToProject():
    '''
    Attach BIDS data files to a project at the session level

    Use this function to dynamically generate files and upload them to the BIDS
    project at the session level. The filename **must** be BIDS valid. Examples
    include the README or CHANGES file.

    This function takes no input but **must** return a dictionary (or list of dictionaries) with three
    parts:

    1. ``name``: the BIDS filename, with optional keywords for formatting (e.g. ``{subject}``).
    2. ``data``: the data to upload, which **must** be in literal string format.
    3. ``type``: the file MIMEType; see `Link here <https://www.freeformatter.com/mime-types-list.html>`_ for available types.

    :returns: dictionary -- the dictionary containing BIDS data

    Example -- Adding a README:

    >>> def AttachToSession():
    ...     attachment1 = {
    ...         'name': 'README',
    ...         'data': 'This is my BIDS dataset',
    ...         'type': 'text/plain'
    ...     }
    ...     return attachment1

    >>> AttachToSession()
    {'name': 'README', 'data': 'This is my BIDS dataset', 'type': 'text/plain'}
    '''
    return
