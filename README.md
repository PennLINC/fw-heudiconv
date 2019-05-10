# Heudiconv-Style BIDS curation for Flywheel

If running as a CLI:

1. Make sure you have the [Flywheel CLI](https://docs.flywheel.io/hc/en-us/articles/360008162214-Installing-the-Command-Line-Interface-CLI-) and [SDK](https://pypi.org/project/flywheel-sdk/) installed. Note that this is `flywheel-sdk` and NOT `flywheel`.

2. Download the package from pip

`pip install fw-heudiconv`

OR

[Clone or download this repository](https://github.com/PennBBL/fw-heudiconv) to your machine.

If running on Flywheel:
1. Install the `fw-heudiconv` gear.

2. Design your heuristic file

3. Run `fw-heudiconv`

`fw-heudiconv-curate` to curate the dataset into BIDS

`fw-heudiconv-export` to export the dataset to your machine

`fw-heudiconv-tabulate` to list the sequence information for your dataset

Use the flag --dry_run to test your heuristic.

---
# Overview

`fw-heudiconv` is based on the popular `heudiconv` software, ["a flexible DICOM converter for organizing brain imaging data into structured directory layouts"](https://heudiconv.readthedocs.io/en/latest/). `heudiconv` makes use of a user defined heuristic — a discrete set of rules — to standardise naming conventions within the user's project directory. On Flywheel, where processes, analyses, and curation are all automated in the context of BIDS, correct naming is critical. Leveraging `heudiconv`'s conventions and philosophy, `fw-heudiconv` allows users to systemmatically and consistently curate BIDS-valid datasets on Flywheel with most of the bells and whistles included. For an in-depth walkthrough of `heudiconv`, check out [this example](http://reproducibility.stanford.edu/bids-tutorial-series-part-2a/) from Stanford.

# What is a Heuristic?

As mentioned previously, a heuristic is a discrete set of rules specifying how to name different imaging files in a directory, based on properties in the image header. For `fw-heudiconv`, this set of rules is best specified in a python file. Here's an example:

```
#!/usr/bin/env python
"""Heuristic for mapping Brain RF1 scans into BIDS"""
import os


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


# Baseline session
t1w = create_key(
    'sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
t2w = create_key(
    'sub-{subject}/{session}/anat/sub-{subject}_{session}_T2w')

# ASL Scans
mean_perf = create_key(
    'sub-{subject}/{session}/asl/sub-{subject}_{session}_CBF')
raw_asl = create_key(
    'sub-{subject}/{session}/asl/sub-{subject}_{session}_asl')
m0 = create_key(
    'sub-{subject}/{session}/asl/sub-{subject}_{session}_MZeroScan')

# tms session
# conditions (run 1)
nback_HiConHiLoWMgated_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_'
    'task-nback_acq-HiConHiLoWMgated_run-01_bold')
# conditions (run 2)
nback_HiConHiLoWMgated_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_'
    'task-nback_acq-HiConHiLoWMgated_run-02_bold')

# field map
fmap_run1_ph = create_key(
    'sub-{subject}/{session}/fmap/sub-{subject}_{session}_run-01_phasediff')
fmap_run1_mag = create_key(
    'sub-{subject}/{session}/fmap/sub-{subject}_{session}_run-01_magnitude{item}')

# task session
# field maps (C412 ONLY)
fmap_pa_run1 = create_key(
    'sub-{subject}/{session}/fmap/sub-{subject}_{session}_dir-PA_run-01_epi')
fmap_ap_run1 = create_key(
    'sub-{subject}/{session}/fmap/sub-{subject}_{session}_dir-AP_run-01_epi')

# **********************************************************************************
def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    last_run = len(seqinfo)

    info = {
        # baseline
        t1w: [], t2w: [], mean_perf: [], qsm_ph: [], qsm_mag: [],

        # TMS scans
        nback_HiConHiLoWMgated_run1: [],
        nback_HiConHiLoWMgated_run2: [],

        # field map
        fmap_run1_ph: [], fmap_run1_mag: [],

        # task
        fmap_pa_run1: [], fmap_ap_run1: [],
    }

    for s in seqinfo:
        protocol = s.protocol_name.lower()

        # Baseline Anatomicals
        if "anat_t1w" in protocol:
            info[t1w].append(s.series_id)
        elif "anat_t2w" in protocol:
            info[t2w].append(s.series_id)

        # TMS day
        elif "task-nback_acq-HiConHiLoWMgated_run-01" in s.protocol_name:
            info[nback_HiConHiLoWMgated_run1].append(s.series_id)
        elif "task-nback_acq-LoConHiLoWMgated_run-01" in s.protocol_name:
            info[nback_LoConHiLoWMgated_run1].append(s.series_id)

        # fmaps for subject C412
        elif "fmap_run-01" in protocol and "M" in s.image_type:
            info[fmap_run1_mag].append(s.series_id)
        elif "fmap_run-01" in protocol and "P" in s.image_type:
            info[fmap_run1_ph].append(s.series_id)

        elif "task-rest_acq-gated_bold" in s.protocol_name:
            info[rest_gated].append(s.series_id)

        elif "fmap_run-02" in protocol and "M" in s.image_type:
            info[fmap_run2_mag].append(s.series_id)
        elif "fmap_run-02" in protocol and "P" in s.image_type:
            info[fmap_run2_ph].append(s.series_id)

        elif "task-nback_acq-HiConHiLoWMgated_run-02" in s.protocol_name:
            info[nback_HiConHiLoWMgated_run2].append(s.series_id)
        elif "task-nback_acq-LoConHiLoWMgated_run-02" in s.protocol_name:
            info[nback_LoConHiLoWMgated_run2].append(s.series_id)

        # Task day
        # **** for subject C412 only ****
        elif "acq-fMRIdistmap_dir-PA_run-01" in s.protocol_name:
            info[fmap_pa_run1].append(s.series_id)
        elif "acq-fMRIdistmap_dir-AP_run-01" in s.protocol_name:
            info[fmap_ap_run1].append(s.series_id)

    return info


# Any extra metadata that might not be automatically added by dcm2niix. H
MetadataExtras = {
    fmap_run1_ph: {
        "EchoTime1": 0.004,
        "EchoTime2": 0.006
    }
}


IntendedFor = {
    # baseline
    dwi_rpe: [
        'sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-HASC55_run-01_dwi.nii.gz',
        'sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-HASC55_run-02_dwi.nii.gz',
        'sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-HASC92_dwi.nii.gz',
        'sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-RAND57_dwi.nii.gz'],

    # task visit
    fmap_pa_run1: [ 'sub-{subject}/{session}/func/sub-{subject}_{session}_task-flanker_bold' ],
    fmap_ap_run1: [ 'sub-{subject}/{session}/func/sub-{subject}_{session}_task-flanker_bold' ]

}
```

There's a lot going on here, so let's break it down.

## Heuristic Breakdown: create_key()

This is the heavy lifting on the user's side. This function defines the template for a naming convention that the user wants to eventually to be filled in. For example, to create a BIDS compliant T1 name:

```
t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
```

In this line, the characters within `{}` are to be filled with case-specific values. You can use `create_key()` to create any number of keys for any number of different scan types, as long as you can fill in the fields for every that will meet the corresponding criteria.

```
nback_HiConHiLoWMgated_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_'
    'task-nback_acq-HiConHiLoWMgated_run-01_bold')
```

## Heuristic Breakdown: infotodict()

This function does the heavy lifting on the computational side. This function extracts sequence information (e.g. from the image header) so that the user can specify to which template the image goes to. The object `info` is a dictionary, where we store lists of all of the scans that belong to a certain template. For example, the T1 we specified earlier:

```
if "anat_t1w" in protocol:
    info[t1w].append(s.series_id)
```

The T1 scan (which is an object called `s`) has a property named `protocol`. This protocol field, for all T1 scans, *should* contain the text "anat_t1w". If this is the case, `s` will be added to the appropriate list in the dictionary.

If this is confusing, don't be discouraged — much of this process is abstracted very well by `heudiconv`; all that is required of the user is to know what properties in their scans' headers best discriminate different scans, and to express that in a series of `if-else` statements (see the full heuristic example). For example, if you know your protocol "*n*-back" has the string "back", in it, you will always be able to do:

```
if "back" in protocol:
```

And then further refine the match using other fields:

```
if "back" in protocol:
    if "M" in image_type:
        #assign to the correct template
```

## How Do I Know What Discriminates My Scans?

Understanding the different fields in your scans, and the values that they can take, will help you write a good heuristic. To do this, you need a **sequence info table**. In `fw-heudiconv` this is provided by the `fw-heudiconv` gear, by setting the "**Action**" flag to "**Tabulate**". The output will be a .tsv file that you can use to examine all of the unique values in the scan's header fields. [Here's](http://reproducibility.stanford.edu/wp-content/uploads/2018/03/dicominfo_25.png) an example of what that could look like.

## Metadata, Fieldmap Intentions, & Extended BIDS

One advantage of `fw-heudiconv` is that we can use it to specify BIDS metadata that normally wouldn't be added through `heudiconv`. This can be any field you want to specify, for example setting `EchoTime1` and `EchoTime2` for fieldmaps with phase diffs:
```
MetadataExtras = {
    fmap_run1_ph: {
        "EchoTime1": 0.004,
        "EchoTime2": 0.006
    }
}
```

As you can see, it's simply a dictionary with values you want to be added to certain templates (in this case, the template for `fmap_run1_ph`).

Additionally, with this method we can specify the list of files for which fieldmaps are intended:
```
fmap_ap_run1: [ 'sub-{subject}/{session}/func/sub-{subject}_{session}_task-flanker_bold' ]
```

If you have other templates (e.g. asl) that are not currently covered by the official BIDS specifications, you can add special metadata to these templates in this section too.
