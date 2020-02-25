#!/usr/bin/env python
import json
import flywheel
import os
import shutil
import logging
from fw_heudiconv.cli import export


# logging stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-gear')
logger.info("{:=^70}\n".format(": fw-heudiconv gear manager starting up :"))

# start up inputs
invocation = json.loads(open('config.json').read())
config = invocation['config']
inputs = invocation['inputs']
destination = invocation['destination']
key = inputs['api_key']['key']
fw = flywheel.Client(key)
user = fw.get_current_user()

# start up logic:
analysis_container = fw.get(destination['id'])
project_container = fw.get(analysis_container.parents['project'])
project_label = project_container.label
dry_run = config['dry_run']
action = config['action']

# try get heuristic from the file; if not present, check for default heuristic
heuristic = export.get_nested(inputs, 'heuristic', 'location', 'path')
if heuristic is None:
    heuristic = export.get_nested(config, 'default_heuristic')

if not bool(heuristic) and action == "Curate":
    logger.error("You must either supply a heuristic file in the input tab, or type in the correct name of default heuristic from the HeuDiConv module in the config tab. See https://github.com/nipy/heudiconv/tree/master/heudiconv/heuristics.")
    raise ValueError("No heuristic given!")

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
logger.info("Calling fw-heudiconv with the following settings:")
logger.info("Project: {}".format(project_label))
logger.info("Subject(s): {}".format(subjects))
logger.info("Session(s): {}".format(sessions))
logger.info("Heuristic: {}".format(heuristic))
logger.info("Action: {}".format(action))
logger.info("Dry run: {}".format(dry_run))

# action
call = "fw-heudiconv-{} --verbose --api-key {} --project {}".format(action.lower(), key, project_label.replace(" ", "\ "))

if dry_run:
    call  = call + " --dry-run"

if subjects:
    call = call + " --subject {}".format(" ".join(subjects))
if sessions:
    call = call + " --session {}".format(" ".join(sessions))

if heuristic and action.lower() == "curate":
    call = call + " --heuristic {}".format(heuristic)

elif action.lower() == "export":
    call = call + " --destination {}".format("/flywheel/v0/output")

elif action.lower() == "meta":
    call = call + " --autogen-participants-meta --autogen-sessions-meta"

elif action.lower() == "validate":
    call = call + " --flywheel --directory {}".format("/flywheel/v0/output")

elif action.lower() == "tabulate":
    call = call + " --path {}".format("/flywheel/v0/output")

elif action.lower() == "reproin":
    call = call + " --protocol-names {}".format(heuristic)

os.system(call)

if action.lower() in ["export", "tabulate"]:

    logger.info("Tidying output data...")
    output_dir = "/flywheel/v0/output"
    os.system("zip -r {0}/{1}_{2}.zip {0}/*".format(output_dir, destination['id'], action.lower()))

    to_remove = os.listdir(output_dir)
    to_remove = ["{}/{}".format(output_dir, x) for x in to_remove if ".zip" not in x]
    for x in to_remove:
        if os.path.isfile(x):
            os.remove(x)
        else:
            shutil.rmtree(x)

logger.info("Done!")
logger.info("{:=^70}\n".format(": Exiting fw-heudiconv gear manager :"))
