# netbox-proxmox-ingester
![Static Badge](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)

`netbox-proxmox-ingester` is a work-in-progress Python package intended to ingest
virtual machine information from Proxmox VE into NetBox.

At a high level, the project retrieves data from Proxmox VE, validates and
transforms that data, and then creates or updates the corresponding objects in
NetBox. The long-term goal is to provide a reliable, repeatable ingestion
pipeline that can be used both interactively and, eventually, as part of a
NetBox plugin.

⚠️ **Status: Work in Progress** ⚠️

This project is under active development and should currently be considered
experimental. Interfaces, behavior, and internal structure are likely to change.

## Current state
At present, the repository primarily contains a proof-of-concept implementation
in `sample_implementation.py`.

This file is intentionally rough and procedural. Its purpose is **not** to serve as
production-ready code, but to demonstrate and validate the end-to-end process
flow:

- Gathering data from Proxmox VE  
- Normalizing and validating that data  
- Performing calculations and transformations  
- Creating the corresponding objects inside NetBox  

The PoC exists to prove that this flow works reliably before the codebase is
refactored into a clean, installable library with a stable CLI interface.

## What this project does (and will do)
The ingestion process focuses on the following high-level stages:

- Retrieve the following information from Proxmox VE:
    - Clusters
    - Nodes
    - Virtual Machines
    - VM configuration, including disk and network information
- Validate and normalize raw data  
- Perform unit conversions and derived calculations  
- Persist intermediate state for review and inspection  
- Create or update NetBox objects using backend logic  

## Assumptions and prerequisites
The current PoC implementation makes a number of assumptions about the environment:

1. Proxmox VE is already deployed and accessible.
2. The prerequisite libraries are already installed, preferably in a Python virtual
   environment. Details can be found in `requirements.txt`. Currently, installing these
   are outside the scope of this document.
3. Relevant NetBox objects such as sites and virtualization infrastructure already exist.
4. Proxmox node names correspond to the relevant NetBox objects.

Discovery and ingestion of prerequisite infrastructure data is out of scope for
this PoC implementation at present. Supporting tooling may be published separately in
the future.

## Contributions and Contact
Although this is a public repository, this project is not currently open for contributions. 
However, this status will more than likely change in future.

For any questions, queries or anything else, pleae do not hesitate to contact me via GitHub.

## Licensing
This project is licensed under the Apache License, Version 2.0.
See the `LICENSE` file for details.
