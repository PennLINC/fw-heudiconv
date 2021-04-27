'''
Use this file to initialise data used for unittesting different modules.

The unittests will be run by doctest

'''


# data for curate module
def create_seqinfo():

    return

def create_reproin_test_strings():

    strings = [
    'anat-localizer',
    'anat-AAHScout',
    'anat-Localizer-aligned',
    'anat-T1w',
    'func-BOLD_task-rest4min_run-1_dir-AP_seq-CMRR',
    'fmap-BOLD-SpinEchoFieldMap_dir-AP_seq-CMRR',
    'func-BOLD_task-rest4min_run-1_dir-PA_seq-CMRR',
    'fmap-BOLD-SpinEchoFieldMap_dir-PA_seq-CMRR',
    'func-BOLD_task-rest4min_run-2_dir-AP_seq-CMRR',
    'func-BOLD_task-rest4min_run-2_dir-PA_seq-CMRR'
    ]

    return strings

def create_project_object():

    '''
    Copy-paste project object from the gear testing project, strip out all PHI and unnecessary data.
    Modify as necessary for testing.
    '''

    import datetime

    project_obj = {'analyses': None,
      'created': datetime.datetime(2019, 3, 13, 17, 3, 57, 24000, tzinfo=tzutc()),
      'description': None,
      'editions': None,
      'files': [
                {'classification': {},
                 'created': datetime.datetime(2019, 4, 25, 16, 1, 49, 74000, tzinfo=tzutc()),
                 'hash': 'v0-sha384-9f0c0dfdfa33087286b4b7cbf5986a31a31e7fca42b045b3c0f77b1872999519a6ecf3c9ce5c4024b0a974074126216c',
                 'id': 'e8e5f407-b1d1-46a6-8087-6a30d59265aa',
                 'info': {'BIDS': {'Filename': '',
                                   'Folder': '',
                                   'Path': '',
                                   'error_message': "Filename '' is too short",
                                   'ignore': False,
                                   'template': 'project_file',
                                   'valid': False}},
                 'info_exists': True,
                 'mimetype': 'text/plain',
                 'modality': None,
                 'modified': datetime.datetime(2019, 5, 8, 16, 49, 13, 197000, tzinfo=tzutc()),
                 'name': 'license.txt',
                 'origin': {'id': 'foo@bar.com',
                            'method': None,
                            'name': None,
                            'type': 'user',
                            'via': None},
                 'replaced': None,
                 'size': 65,
                 'tags': [],
                 'type': 'text',
                 'zip_member_count': None},
                {'classification': {},
                 'created': datetime.datetime(2019, 4, 29, 18, 49, 15, 358000, tzinfo=tzutc()),
                 'hash': 'v0-sha384-bdbf04d000b06b26f36f46a731c6ecc83bb52c8a09136a52b7285b8e888f1e8c770f66187d4c4ed9cc7b29498a2d4900',
                 'id': 'e0e37f1b-f7c3-4afb-b48e-1e994bf1cdd5',
                 'info': {'BIDS': {'Filename': '',
                                   'Folder': '',
                                   'Path': '',
                                   'error_message': "Filename '' is too short",
                                   'ignore': False,
                                   'template': 'project_file',
                                   'valid': False}},
                 'info_exists': True,
                 'mimetype': 'text/x-python',
                 'modality': None,
                 'modified': datetime.datetime(2019, 5, 8, 16, 49, 13, 214000, tzinfo=tzutc()),
                 'name': 'sample_heuristic.py',
                 'origin': {'id': 'foo@bar.com',
                            'method': None,
                            'name': None,
                            'type': 'user',
                            'via': None},
                 'replaced': None,
                 'size': 1287,
                 'tags': [],
                 'type': 'source code',
                 'zip_member_count': None},
                ],
      'group': 'bbl',
      'id': '5c8937fddf93e3002e025e2b',
      'info': {'BIDS': {'Acknowledgements': '',
                        'Authors': [],
                        'BIDSVersion': '1.0.0rc4',
                        'DatasetDOI': '',
                        'Funding': '',
                        'HowToAcknowledge': '',
                        'License': 'This dataset is made available under the Public '
                                   'Domain Dedication and License \n'
                                   'v1.0, whose full text can be found at \n'
                                   'http://www.opendatacommons.org/licenses/pddl/1.0/. \n'
                                   'We hope that all users will follow the ODC '
                                   'Attribution/Share-Alike \n'
                                   'Community Norms '
                                   '(http://www.opendatacommons.org/norms/odc-by-sa/); \n'
                                   'in particular, while not legally required, we '
                                   'hope that all users \n'
                                   'of the data will acknowledge the OpenfMRI '
                                   'project and NSF Grant \n'
                                   'OCI-1131441 (R. Poldrack, PI) in any '
                                   'publications.',
                        'Name': 'Mixed-gambles task',
                        'ReferencesAndLinks': 'Tom, S.M., Fox, C.R., Trepel, C., '
                                              'Poldrack, R.A. (2007). The neural '
                                              'basis of loss aversion in '
                                              'decision-making under risk. Science, '
                                              '315(5811):515-8',
                        'template': 'project'}},
      'info_exists': True,
      'label': 'gear_testing',
      'modified': datetime.datetime(2020, 2, 7, 17, 19, 27, 754000, tzinfo=tzutc()),
      'notes': [],
      'parents': {'acquisition': None,
                  'analysis': None,
                  'group': 'bbl',
                  'project': None,
                  'session': None,
                  'subject': None},
      'permissions': [{'access': 'admin', 'id': 'foo@bar.com'},],
      'providers': None,
      'revision': 1133,
      'tags': [],
      'templates': None}
