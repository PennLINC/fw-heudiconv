import os
"""
info = {
    (
        '{bids_subject_session_dir}/dwi/{bids_subject_session_prefix}_acq-multishell_dir-AP_dwi_dwi__dup-02',
        ('nii.gz', 'dicom'),
        None
    ): [None]
}
id = {'locator': 'unknown', 'session': 'None', 'subject': '20448'}
"""
def convert(info):
    """Using an id and an info object, will format it into a flywheel BIDS
    standard object

    Args:
        _id (dict): The dictionary returned from the infotoid
        info (dict): The info returned from the infotodict function
    Returns:
        dict: A BIDS namespace update to send via sdk
    """
    for info_key in info.keys():
        bids_subject_session_dir = 'sub-{}/sub-{}'.format(_id['subject'], _id['session'] if _id['session'] not in ['None', None] else 'sub-{}'.format(_id['subject']),
        bids_subject_session_prefix = bids_subject_session_dir.replace('/', '_')

        full_path = info_key[0].format({
            'bids_subject_session_dir': bids_subject_session_dir,
            'bids_subject_session_prefix': bids_subject_session_prefix
        })

        BIDS = {
            'Filename': os.path.basename(full_path),
            'Path': os.path.dirname(full_path),
            'Folder': info_key.split('/')[1],
            'valid': True,
            'ignore': 'dup' in os.path.basename(full_path)
        }
