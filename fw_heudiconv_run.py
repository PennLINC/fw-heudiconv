#!/usr/bin/env python

import json, codecs

print('This is an example python script.')
invocation  = json.loads(open('config.json').read())
config      = invocation['config']
inputs      = invocation['inputs']
destination = invocation['destination']


# Display everything provided to the job

def display(section):
	print(json.dumps(section, indent=4, sort_keys=True))

print('\nConfig:')
display(config)
print('\nDestination:')
display(destination)
print('\nInputs:')
display(inputs)


# Check if the flywheel SDK is installed
try:
	import flywheel

	# Make some simple calls to the API
	fw = flywheel.Flywheel(inputs['api-key']['key'])
	user = fw.get_current_user()
	config = fw.get_config()

	print('You are logged in as ' + user.firstname + ' ' + user.lastname + ' at ' + config.site.api_url[:-4])

except ImportError:
	print('\nFlywheel SDK is not installed, try "fw gear modify" and then "pip install flywheel-sdk".\n')


# Check if requests is installed
try:
	import requests

	# Find out how many people are in space \o/
	r = requests.get(
		'https://www.howmanypeopleareinspacerightnow.com/peopleinspace.json',

		headers={
			'Host': 'www.howmanypeopleareinspacerightnow.com',
			'User-Agent': 'curl/7.47.0',
			'Accept': '*/*',
		},
	)

	# Save astronaut data as metadata
	if r.ok:
		data = r.json()
		astronauts = data['people']

		print("There are " + str(len(astronauts)) + " in space today:")
		for astronaut in astronauts:
			print("\t" + astronaut['name'])

		metadata = {
			'session' : {
				'info': {
					'astronauts': astronauts
				}
			}
		}

		with open('output/.metadata.json', 'wb') as f:
		    json.dump(metadata, codecs.getwriter('utf-8')(f), ensure_ascii=False)

	else:
		# Might be that the API is down today. Check to see if we still have a space program?
		print('Not sure how many people are in space :(')
		print()
		print(r.text)


except ImportError:
	print('\nRequests is not installed, try "fw gear modify" and then "pip install requests".\n')
