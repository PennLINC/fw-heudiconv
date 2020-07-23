***********************************
Tips & Tricks: Curating Creatively
***********************************

Because ``fw-heudiconv`` is built in Python, you have access to anything Python
can do when you build your heuristic (as long as you use the special functions
and data structures). Here, we show a few fun ways we've used Python to solve
a few tricky heuristic challenges.

Dynamically Replacing Subject/Session Labels
============================================

It might be useful to dynamically replace a Flywheel subject's label with some
other label in BIDS — for example, in the event that you need to withhold personally
identifying information from a BIDS output you share, but still keep the original
Flywheel subject's label, for consistency. Well this can be accomplished in the
``Replace*()`` functions using a DataFrame with ``pandas``. If you're running
``fw-heudiconv`` from disk, you can read in a file at the same time that the
heuristic is parsed:

.. code-block:: python

    def ReplaceSubject(label):

        import pandas as pd

        df = pd.read_csv('DeIdentifiedNames.csv')

And then filter your DataFrame as necessary:

.. code-block:: python

    def ReplaceSubject(label):

        import pandas as pd

        df = pd.read_csv('DeIdentifiedNames.csv')
        target = df[(df.first_name == "Jason")]
        replacement = target['new_ID'].values[0]

        return str(replacement)

Arterial Spin Labelling Data
============================

ASL is a BIDS protocol proposal that is fast on its way to being accepted into
the official BIDS spec, but is still being reviewed and updated. At present,
ASL in BIDS requires a special kind of events file, the *aslcontext* file. This
is a TSV file not unlike the *events.tsv* file given for BOLD task data, but is used
in this case to denote the order of label vs. control in the volumes. The file
might look like this:

.. code-block::

    volume_type
    control
    label
    control
    label
    control
    label
    control
    label
    control
    label
    control
    label
    control
    label

For this purpose, we can use the ``AttachToSession()`` function. You *could* do as
above and read in a file on disk *within* the function, but you could be even
cleverer and instead dynamically create this file:

.. code-block:: python

    def AttachToSession():

        NUM_VOLUMES=10
        data = ['control', 'label'] * NUM_VOLUMES
        data = '\n'.join(data)
        data = 'volume_type\n' + data # the data is now a string; perfect!

        output_file = {

          'name': '{subject}_{session}_aslcontext.tsv',
          'data': data,
          'type': 'text/tab-separated-values'
        }

        return output_file

This could be especially useful if you don't want to rely on external data files to curate your project.
You can find out the correct number of LABEL-CONTROL pairs from the DICOM header info found in the output of ``fw-heudiconv-tabulate``,
which will also help you hard code the extra ASL metadata and insert it into the ``MetadataExtras`` variable.

DataFrames to Strings
=====================

Since the ``AttachTo*()`` functions can only return string data, how would you attach
a DataFrame object? It's pretty simple actually:

.. code-block:: python

    def AttachToSession():

        # example: uploading multiple files -- a json, and a TSV
        import json

        adict = {
            "id": "04",
            "name": "foo",
            "scan": "blah"
        }

        json_object = json.dumps(adict, indent = 4)

        attachment1 = {
            'name': 'jsonexample.json',
            'data': json_object,
            'type': 'application/json'
        }
        import pandas as pd
        raw_data = {'first_name': ['Jason', 'Molly', 'Tina', 'Jake', 'Amy'],
            'last_name': ['Miller', 'Jacobson', 'Ali', 'Milner', 'Cooze'],
            'age': [42, 52, 36, 24, 73],
            'preTestScore': [4, 24, 31, 2, 3],
            'postTestScore': [25, 94, 57, 62, 70]}
        df = pd.DataFrame(raw_data, columns = ['first_name', 'last_name', 'age', 'preTestScore', 'postTestScore'])

        attachment2 = {
            'name': '{subject}/{session}/perf/{subject}_{session}_aslcontext.tsv',
            'data': df.to_csv(index=False, sep='\t'), # .to_csv() with no file argument returns a string!
            'type': 'text/tab-separated-values'
        }

        # this is also an opportunity to demonstrate how to attach multiple files -- just use a list!
        return [attachment1, attachment2]
