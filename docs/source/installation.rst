Installation
=============


To use locally, follow instructions below to set up your system for using ``fw-heudiconv`` on your machine:

Estimated time: 15 minutes

Install & start up Miniconda
----------------------------

First, get a package management system. Recommended is miniconda (conda): **Conda quickly installs, runs and updates packages and their dependencies.**

https://docs.conda.io/en/latest/miniconda.html.

You can check if you have this successfully by going to the terminal and doing: ::

    $ which conda [macOS]

Start a virtual environment
---------------------------

Use miniconda to create a virtual environment, a restricted workspace where your programs and processes can operate without affecting everything on your computer. Create an environment called flywheel, in the terminal: ::

    $ conda create -n flywheel anaconda python=3

At the prompt for which packages to install, type y and hit enter. It’s better to have them all, and they will not take up a lot of space on your machine: ::

    :
    :
    :
    $ wurlitzer          pkgs/main/osx-64::wurlitzer-1.0.2-py37_0
    $ xlrd               pkgs/main/osx-64::xlrd-1.2.0-py37_0
    $ xlsxwriter         pkgs/main/noarch::xlsxwriter-1.1.8-py_0
    $ xlwings            pkgs/main/osx-64::xlwings-0.15.8-py37_0
    $ xlwt               pkgs/main/osx-64::xlwt-1.3.0-py37_0
    $ xz                 pkgs/main/osx-64::xz-5.2.4-h1de35cc_4
    $ yaml               pkgs/main/osx-64::yaml-0.1.7-hc338f04_2
    $ zeromq             pkgs/main/osx-64::zeromq-4.3.1-h0a44026_3
    $ zict               pkgs/main/noarch::zict-1.0.0-py_0
    $ zipp               pkgs/main/noarch::zipp-0.5.1-py_0
    $ zlib               pkgs/main/osx-64::zlib-1.2.11-h1de35cc_3
    $ zstd               pkgs/main/osx-64::zstd-1.3.7-h5bba6e5_0


    $ Proceed ([y]/n)?

Activate your environment, so that any packages you install or use stay restricted to this project: ::

    $ source activate flywheel

Download ``fw-heudiconv`` from pip
----------------------------------

The ``fw-heudiconv`` code is hosted on pip: **pip is a standard package-management system used to install and manage software packages written in Python**

Pip should be installed with your new environment, but you can ensure you have it by running: ::

    $ which pip

Now, use pip to install ``fw-heudiconv``: ::

    $ pip install fw-heudiconv

Download the Flywheel SDK & CLI
---------------------------------

You will need to download the flywheel software development kit in order to use ``fw-heudiconv``. Follow the instructions `here <https://pypi.org/project/flywheel-sdk/>`_ to install, or run:  ::

    $ pip install flywheel-sdk


The flywheel CLI allows ``fw-heudiconv`` (or any other program you write) to communicate with Flywheel’s database. Follow their instructions `here <https://docs.flywheel.io/hc/en-us/articles/360008162214>`_ to download and login.

Once installed and logged in, you should see your username when you run the following: ::

    $ fw status
    $ You are currently logged in as Tinashe Tapera to https://upenn.flywheel.io


Updating ``fw-heudiconv``
--------------------------

If you already have ``fw-heudiconv`` and wish to update to the latest version, just run: ::

    $ pip install --upgrade fw-heudiconv

Appendix — ``fw-heudiconv-validate``
-------------------------------------

``fw-heudiconv-validate`` is a convenience tool that wraps the official Bids Validator and pipes the output of ``fw-heudiconv-export`` to it. It's most useful for validating Flywheel data through a gear on the GUI.

To use ``fw-heuduiconv-validate`` on your local machine, you need to install `node.js <https://nodejs.org/en/>`_. This is not necessary, however, and instead you are welcome to use ``fw-heudiconv-validate`` on your Flywheel site, or, use ``fw-heudiconv-export`` to export data first, and then use the official Bids Validator available `here <http://bids-standard.github.io/bids-validator/>`_.
