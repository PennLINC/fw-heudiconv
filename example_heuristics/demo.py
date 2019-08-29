import os

# define the create key function
def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

# Create Keys

# eg T1 scans
t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')

# define the infotodict looping function
def infotodict(seqinfo):

    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    # create a dict of your keys
    info = {
        t1w: []
    }
    
    # loop through your scans, if found, add this key to the end of the list in the info dict
    for s in seqinfo:
        protocol = s.protocol_name.lower()
        # t1
        if "mprage" in protocol:
            info[t1w].append(s.series_id)
        else:
            print("Series not recognized!: ", s.protocol_name, s.dcm_dir_name)
    
    return info
