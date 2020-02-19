import os

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

# structurals
t1w = create_key(
    'sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
t2w = create_key(
     'sub-{subject}/{session}/anat/sub-{subject}_{session}_T2w')
flair = create_key(
    'sub-{subject}/{session}/anat/sub-{subject}_{session}_FLAIR')
# task fMRI
object_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-object_run-01_bold')
object_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-object_run-02_bold')
rhyme_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-rhyme_run-01_bold')
rhyme_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-rhyme_run-02_bold')
scenemem_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-scenemem_run-01_bold')
scenemem_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-scenemem_run-02_bold')
sentence_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-sentence_run-01_bold')
sentence_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-sentence_run-02_bold')
wordgen_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-wordgen_run-01_bold')
wordgen_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-wordgen_run-02_bold')
binder_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-binder_run-01_bold')
binder_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-binder_run-02_bold')
verbgen_run1 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-verbgen_run-01_bold')
verbgen_run2 = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-verbgen_run-02_bold')
rest = create_key(
    'sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_bold')

# ASL scans
asl = create_key(
     'sub-{subject}/{session}/asl/sub-{subject}_{session}_asl')
m0 = create_key(
    'sub-{subject}/{session}/asl/sub-{subject}_{session}_MZeroScan')
mean_perf = create_key(
    'sub-{subject}/{session}/asl/sub-{subject}_{session}_CBF')

# Field maps
b0_mag = create_key(
   'sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude{item}')
b0_phase = create_key(
   'sub-{subject}/{session}/fmap/sub-{subject}_{session}_phasediff')


def infotodict(seqinfo):

    last_run = len(seqinfo)

    info = {t1w:[], t2w:[], flair:[], object_run1: [], object_run2: [], rhyme_run1: [],
            rhyme_run2: [], scenemem_run1: [], scenemem_run2: [], sentence_run1: [],
            sentence_run2: [], wordgen_run1: [], wordgen_run2: [], binder_run1: [],
            binder_run2:[], verbgen_run1: [], verbgen_run2: [], rest: [], asl: [],
            m0: [], mean_perf: [], b0_phase: [], b0_mag: []}

# sometimes patients struggle with a task the first time around (or something
# else goes wrong and often some tasks are repeated. This function accomodates
# the variable number of task runs
    def get_both_series(key1, key2, s):
         if len(info[key1]) == 0:
             info[key1].append(s.series_id)
         else:
             info[key2].append(s.series_id)

# this doesn't need to be a function but using it anyway for aesthetic symmetry
# with above function
    def get_series(key, s):
            info[key].append(s.series_id)

    for s in seqinfo:
        protocol = s.protocol_name.lower()
        if any(id in protocol for id in ["t1w", "t1", "mprage_t"]):
            get_series(t1w,s)
        elif "flair" in protocol:
            get_series(flair,s)
        elif any(id in protocol for id in ["t2w", "t2"]):
            get_series(t2w,s)
        elif "object" in protocol:
            get_both_series(object_run1,object_run2,s)
        elif "rhyming" in protocol:
            get_both_series(rhyme_run1,rhyme_run2,s)
        elif "scenemem" in protocol:
            get_both_series(scenemem_run1,scenemem_run2,s)
        elif "sentence" in protocol:
            get_both_series(sentence_run1, sentence_run2, s)
        elif "wordgen" in protocol:
            get_both_series(wordgen_run1,wordgen_run2,s)
        elif "binder" in protocol:
            get_both_series(binder_run1, binder_run2,s)
        elif "verbgen" in protocol:
            get_both_series(verbgen_run1, verbgen_run2,s)
        elif "rest" in protocol:
            get_series(rest,s)
        elif "spiral" in protocol:
            if s.series_description.endswith("_ASL"):
                get_series(asl,s)
            elif s.series_description.endswith("_M0"):
                get_series(m0,s)
        elif "b0map" in protocol:
                if "P" in s.image_type:
                    get_series(b0_phase,s)
                elif "M" in s.image_type:
                    get_series(b0_mag,s)

    return info

MetadataExtras = {
   b0_phase: {
       "EchoTime1": 0.00507,
       "EchoTime2": 0.00753
   }
}

IntendedFor = {
    b0_phase: [
    '{session}/func/sub-{subject}_{session}_task-object_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-object_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-rhyme_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-rhyme_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-scenemem_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-scenemem_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-sentence_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-sentence_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-wordgen_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-wordgen_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-binder_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-binder_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-verbgen_run-01_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-verbgen_run-02_bold.nii.gz',
    '{session}/func/sub-{subject}_{session}_task-rest_bold.nii.gz'],

    m0: [ '{session}/asl/sub-{subject}_{session}_asl.nii.gz' ],
}
