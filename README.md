# netbox-proxmox-ingester

This is a sample implementation to ingest Proxmox VE VM information into Netbox using the Proxmoxer
library to gather information and then uses the NetBox API to igest the data itself. This script 
makes a number of assumptions:

1. The Proxmoxer library is already installed in your environment, ideally in a Python VENV.
2. The various underlying components, such as the VM environment servers are already created.
3. The names of these servers and related correspond to the names of Proxmox nodes.
4. IP Address prefixes have already been created in NetBox.

If you need to have these created as well we will be, in due course, be publishing a series of scripts
to allow you to gather and ingest this information as well.

Besides the assumptions and exclusions already listed, this script will gather and ingest the following information:
