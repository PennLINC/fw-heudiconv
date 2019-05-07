#!/usr/bin/env python
import json
import flywheel
import os
import shutil
import logging
from fw_heudiconv.cli import curate, export, tabulate


# logging stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-gear')
logger.info("=======: fw-heudiconv starting up :=======")

# start up inputs
invocation = json.loads(open('config.json').read())
config = invocation['config']
inputs = invocation['inputs']
destination = invocation['destination']

fw = flywheel.Flywheel(inputs['api-key']['key'])
user = fw.get_current_user()

# start up logic:
heuristic = inputs['heuristic']['location']['path']
analysis_container = fw.get(destination['id'])
project_container = fw.get(analysis_container.parents['project'])
project_label = project_container.label
dry_run = config['dry_run']

# whole project, single session?
do_whole_project = config['do_whole_project']

if not do_whole_project:

    # find session object origin
    session_container = fw.get(analysis_container.parent['id'])
    sessions = [session_container.label]
    # find subject object origin
    subject_container = fw.get(session_container.parents['subject'])
    subjects = [subject_container.label]

else:
    sessions = None
    subjects = None

# logging stuff
logger.info("Running fw-heudiconv with the following settings:")
logger.info("Project: {}".format(project_label))
logger.info("Subject(s): {}".format(subjects))
logger.info("Session(s): {}".format(sessions))
logger.info("Heuristic found at: {}".format(heuristic))
logger.info("Action: {}".format(config['action']))
logger.info("Dry run: {}".format(dry_run))

# action
if config['action'] == "Curate":

    curate.convert_to_bids(fw, project_label, heuristic, subjects, sessions, dry_run=dry_run)

elif config['action'] == "Export":

    downloads = export.gather_bids(fw, project_label, subjects, sessions)
    export.download_bids(fw, downloads, "/flywheel/v0/output", dry_run=dry_run)

    if not dry_run:

        # tidy up
        output_dir = "/flywheel/v0/output"
        os.system("zip -r {}_BIDSexport.zip output/*".format(destination['id']))
        os.system("mv *.zip output")
        to_remove = os.listdir(output_dir)
        to_remove = ["{}/{}".format(output_dir, x) for x in to_remove if ".zip" not in x]
        for x in to_remove:
            if os.path.isfile(x):
                os.remove(x)
            else:
                shutil.rmtree(x)

elif config['action'] == "Tabulate":

    tabulate.tabulate_bids(fw, project_label, "/flywheel/v0/output", subjects, sessions, dry_run=dry_run)

else:

    raise Exception('Action not specified correctly!')
