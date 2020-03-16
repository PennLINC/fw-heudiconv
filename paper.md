---
title: 'FW-HeuDiConv: Heuristic Based Curation of Neuroimaging Data on Flywheel'
tags:
  - Python
  - neuroscience
  - neuroimaging
  - informatics
  - neuroinformatics
authors:
  - name: Tinashe Michael Tapera
    orcid: foo
    affiliation: 1
affiliations:
 - name: foo
   index: 1
date: 13 March 2020
bibliography: paper.bib
---

# Introduction

Data curation in the field of neuroimaging is a fundamental task necessary for creating scalable, reproducible science. To aid in their efforts, researchers have the option to have their data hosted by private vendors, whose infrastructure may mitigate some of the challenges of storing, organising, and tracking massive amounts of data. One such vendor, Flywheel, provides some solutions for this, but researchers ultimately must be able to curate their data themselves on a case-by-case basis to fit scientific standards. In the field of neuroscience, the current standard is the Brain Imaging Data Structure (BIDS) **[REF BIDS HERE]**, an open-source specification of how to store and share neuroimaging files. Flywheel allows users to curate their data using BIDS, but lacks sufficient flexibility for the large variety of use-cases in neuroimaging data collection. `fw-heudiconv` is a toolkit for flexible, reproducible, and user-friendly curation of data on Flywheel's platform.

# Methods & Materials

`fw-heudiconv` is built in Python 3.7 and makes use of the Flywheel Software Development Kit (SDK) to execute the GET and POST requests that allow users to programmatically view and manipulate data on their server. The software also curates data according to the Brain Imaging Data Structure — a data curation paradigm for neuorimaging data that intends to standardise the representation of brain imaging data for research. Importantly,`fw-heudiconv` borrows some of its functionality from `HeuDiConv`, the *Heuristic Dicom Converter* software **[REF HEUDICONV HERE]**, which uses a user-defined heuristic to outline the rules for curating different Nifti files into BIDS format. Lastly, the Flywheel platform gives users the option to develop and deploy analysis or utility pipelines made up of containerised software (via Docker) for provenance and version control, called gears.

# Results

`fw-heudiconv` is available as a command-line tool via PIP **[REF PIP HERE]**, or as a Flywheel Gear that can be launched via their web GUI. The software comprises of a number of feature rich tools for an efficient and reproducible curation workflow. Firstly, after data is uploaded to Flywheel, users make use of the `tabulate` tool, which extracts important sequence information from the DICOM headers of their data, and returns it to the user in a summarised tabular form. After this, users develop a Python heuristic file, which defines the string templates for BIDS compliant filenaming, and outlines through a series of boolean logic how to assign files to their respective templates. Using this heuristic file, users can then use the `curate` tool to test, further develop, and implement their heuristic and apply their proposed changes. For data provenance, users are encouraged to version control their heuristics and can import heuristic files from Github at runtime if desired. At any time, the `clear` tool is available for clearing any existing BIDS data, and since, on Flywheel, BIDS data is supplementary to the user's data, there is no risk of harming the original data through this process. Finally, users can use the `export` tool to download the BIDS data as they curated it, and `validate` tool, which makes use of the BIDS validator **[REF BIDS VALIDATOR HERE]** to ensure the curation is appropriate BIDS.

If users are able to control the naming of sequences at the scanner, `fw-heudiconv` can also automatically curate their data without the need for a heuristic, given that sequence naming follows the ReproIn naming format **[REF REPROIN HERE]**.


# Acknowledgements

# References
