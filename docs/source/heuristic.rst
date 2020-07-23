.. _heuristic:

The Heuristic File
====================
BIDS curation of data on Flywheel is implemented through the use of a heuristic file.
Like the name implies, a heuristic is a set of simple and efficient rules that,
for our purposes, will help map DICOM header info to a BIDS-valid filename.

The heuristic's rules are defined in a Python file which is used as input to the
curate command line tool :mod:`fw_heudiconv.cli.curate`. Since it's Python, it's
possible to accomplish a wide variety of logical operations to define these relationships,
but in order to communicate with Flywheel, ``fw-heudiconv`` expects a few
reserved functions and data structures. These functions are documented below.

.. automodule:: fw_heudiconv.example_heuristics.demo

.. autofunction:: fw_heudiconv.example_heuristics.demo.create_key

.. autofunction:: fw_heudiconv.example_heuristics.demo.infotodict

.. autodata:: fw_heudiconv.example_heuristics.demo.MetadataExtras

.. autodata:: fw_heudiconv.example_heuristics.demo.IntendedFor

.. autofunction:: fw_heudiconv.example_heuristics.demo.ReplaceSubject

.. autofunction:: fw_heudiconv.example_heuristics.demo.ReplaceSession

.. autofunction:: fw_heudiconv.example_heuristics.demo.AttachToSession

.. autofunction:: fw_heudiconv.example_heuristics.demo.AttachToProject
