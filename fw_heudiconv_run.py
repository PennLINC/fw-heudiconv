#!/usr/bin/env python
import json
import flywheel
import os
from fw_heudiconv.cli import curate, export


print('This is an example python script.')
invocation  = json.loads(open('config.json').read())
config      = invocation['config']
inputs      = invocation['inputs']
destination = invocation['destination']

# QUERY ANALYSIS ID TO PASS AS INPUTS TO CURATE.PY or DOWNLOAD.PY

# Display everything provided to the job
def display(section):
    print(json.dumps(section, indent=4, sort_keys=True))

print('\nConfig:')
display(config)
print('\nDestination:')
display(destination)
print('\nInputs:')
display(inputs)

# Make some simple calls to the API
fw = flywheel.Flywheel("upenn.flywheel.io:h5TwSyjISZaqIsqOz0")
user = fw.get_current_user()

# start up logic:
heuristic = inputs['heuristic']['location']['path']
analysis_container = fw.get(destination['id'])
project_container = fw.get(analysis_container.parents['project'])
project_label = project_container.label

# whole project, single session, or many sessions?
do_whole_project = config['do_whole_project']

if not do_whole_project:
    if config['session_ids']:
        sessions = [x.strip() for x in config['session_ids'].split(",")]
    else:
        # find session object origin
        session_container = fw.get(analysis_container.parent['id'])
        sessions = [session_container.label]
    if config['subject_ids']:
        subjects = [x.strip() for x in config['subject_ids'].split(",")]
    else:
        # find subject object origin
        session_container = fw.get(analysis_container.parent['id'])
        subject_container = fw.get(session_container.parents['subject'])
        subjects = [subject_container.label]

else:
    sessions = None
    subjects = None

print(project_label)
print(subjects)
print(sessions)
print(heuristic)

# action
if config['action'] == "Curate":
    print('curate bids')
    curate.convert_to_bids(fw, project_label, heuristic, subjects, sessions)
elif config['action'] == "Export":
    print("export bids")
    downloads = export.gather_bids(fw, project_label, subjects, sessions)
    export.download_bids(fw, downloads, "output")
else:
    raise Exception('Action not specified correctly!')
