#! /usr/bin/env python
#
# Given a Flywheel job id, this script will generate a local testing directory
# within which you can run the job locally, using Docker, as it ran in Flywheel.
#
# This code generates a directory structure that mimics exactly what the Gear would
# get when running in Flywheel. Importantly, this code will generate a "config.json"
# file, which contains all of the metadata the Gear received when running in Flywheel.
#
#  For a given job this script will:
#         1. Make directory structure (gear_job base dir, inputs, outputs)
#         2. Write a valid config.json file
#         3. Download required data to inputs directories
#         4. Generate a shell script that will actually run the job with docker
#            locally (run.sh)
#
# Usage:
#   Positional inputs:
#       [1] - Api Key
#       [2] - Gear Name
#       [3] - Job ID
#       [4] - (Optional) Directory to save job contents. Defaults to cwd.
#
#   fwutil_job_run_local.py <api_key> <job_id> <output_base_directory>
#
# Example:
#   fwutil_job_run_local.py $API_KEY fmriprep 298e73lacbde98273lkad
#
#


import os
import sys
import json
import stat
import flywheel

def build_local_test(job, test_path_root, api_key):
    '''
    Build a local testing instance for a given Flywheel job
    '''

    # Make directories
    test_path = os.path.join(test_path_root, job.gear_info.name + '-' + job.gear_info.version + '_' + job.id)
    input_dir = os.path.join(test_path, 'input')
    output_dir = os.path.join(test_path, 'output')

    if not os.path.isdir(input_dir):
        print('Creating directory: %s' % (input_dir))
        os.makedirs(input_dir)

    if not os.path.isdir(output_dir):
        print('Creating directory: %s' % (output_dir))
        os.mkdir(output_dir)

    # If the job requires an api_key, then add it from the env to the config
    # TODO: Use the base to set the key
    gear = fw.get_gear(job.gear_id).gear
    if gear.inputs.get('api-key', ""):
        job['config']['inputs']['api-key'] = { "key": api_key, "base": "api-key" }
    if gear.inputs.get('key', ""):
        job['config']['inputs']['key'] = { "key": api_key, "base": "api-key" }
    if gear.inputs.get('api_key', ""):
        job['config']['inputs']['api_key'] = { "key": api_key, "base": "api-key" }

    # Write the config file
    config_file = os.path.join(test_path, 'config.json')
    with open(config_file, 'w') as cf:
        json.dump(job['config'], cf, indent=4)


    # For each key in input, make the directory and download the data
    input_data = job.config.get('inputs')

    for k in input_data:

        if k == 'api_key' or k == 'key' or k == 'api-key':
            continue

        _input = input_data[k]

        # Make the directory
        ipath = os.path.join(input_dir, k)
        if os.path.exists(ipath):
            print('Exists: %s' % ipath)
        else:
            os.mkdir(ipath)
            print('Created directory: %s' % ipath)

        # Download the file to the directory
        ifilename = _input['location']['name']
        ifilepath = os.path.join(ipath, ifilename)
        iparentid = _input['hierarchy']['id']

        if os.path.isfile(ifilepath):
            print('Exists: %s' % ifilename)
        else:
            print('Downloading: %s' % ifilename)
            fw.download_file_from_container(iparentid, ifilename, ifilepath)

    print('Done!')

    # Generate docker run command and save to script
    gear_descriptor = gear['custom'].get('docker-image', '')
    if not gear_descriptor:
        gear_descriptor = gear['custom'].get('gear-builder').get('image')

    run_string = ('docker run --rm -ti --entrypoint=/bin/bash -v %s:/flywheel/v0/input -v %s:/flywheel/v0/output -v %s:/flywheel/v0/config.json %s' %
                     (input_dir, output_dir, config_file, gear_descriptor)
                 )
    run_script = os.path.join(test_path, 'run.sh')
    with open(run_script, 'w') as rs:
        rs.write('#! /bin/bash \n\n')
        rs.write(run_string)
        rs.write('\n')

    # Make the file executable
    st = os.stat(run_script)
    os.chmod(run_script, st.st_mode | stat.S_IEXEC)

    print(run_string)


    return test_path, run_script


if __name__=='__main__':
    """
    Given a Flywheel job id, this script will generate a local testing directory
    within which you can run the job locally, using Docker, as it ran in Flywheel.

    Positional inputs:
        [1] - Api Key
        [2] - Gear Name
        [3] - Job ID
        [4] - (Optional) Directory to save job contents. Defaults to cwd.

    """

    if not sys.argv[1]:
        raise ValueError('API KEY required')
    else:
        api_key = sys.argv[1]

    fw = flywheel.Client(api_key)
    if fw.get_current_user().root:
        fw = flywheel.Client(api_key, root=True)
        job = fw.get_job(sys.argv[3])

    # Get the job
    if not job:
        job = [x for x in fw.get_current_user_jobs(gear=sys.argv[2]).jobs if x.id == sys.argv[3]]
        if job:
            job = job[0]
        else:
            raise ValueError('Job could not be found. The ID may not be valid, or it may not be your job!')

    # Build the local test
    if len(sys.argv) == 5:
        test_path_root = sys.argv[4]
    else:
        test_path_root = os.getcwd()

    build_local_test(job, test_path_root, api_key)
