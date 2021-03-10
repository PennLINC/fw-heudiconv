Usage
=====

``fw-heudiconv`` can be run either from the command line, or on Flywheel as a gear.
See below for command line instructions.


Tabulate
--------

.. argparse::
  :ref: tabulate
  :module: fw_heudiconv.cli.tabulate
  :func: get_parser
  :prog: fw-heudiconv-tabulate

Curate
------

.. argparse::
  :ref: curate
  :module: fw_heudiconv.cli.curate
  :func: get_parser
  :prog: fw-heudiconv-curate

Export
------

.. argparse::
  :ref: export
  :module: fw_heudiconv.cli.export
  :func: get_parser
  :prog: fw-heudiconv-export

Validate
--------

.. argparse::
  :ref: validate
  :module: fw_heudiconv.cli.validate
  :func: get_parser
  :prog: fw-heudiconv-validate

Clear
-----

.. argparse::
  :ref: clear
  :module: fw_heudiconv.cli.clear
  :func: get_parser
  :prog: fw-heudiconv-clear

flaudit
-------

``flaudit`` runs as a gear on Flywheel. See the Quick Start guide for usage.
