# NetBox Proxmox Ingestion Sample Implementation
This file was created as a Proof of Concept with two goals in mind:

1. Proof that this process can be completed entirely using API calls to the two systems.
2. Validate the process flow at a high level.

## ⚠️ PLEASE NOTE ⚠️
This is **NOT** a final product and is absolutely not production ready. If you use this in your 
production environment, you do so entirely **at your own risk!**

Furthermore, this script is provided **as is** and no warranties, either tacit or implicit, can 
be made as the safety of running this in a production environment. The Network Entropologist, and 
and/all of their representatives, affiliates, agents, etc. disclaims any and all responsibility for
any and all loss of data, or damage of any other kind whatsoever, that may result from running this 
in a production environment.

**YOU HAVE BEEN WARNED!!**

## Installation
1. Clone this repository locally.
2. Create a Python Virtual Environment.
3. Activate this Virtual Environment.
4. Install the required 3rd party packages.
5. Run the script.

 ```
git clone https://github.com/NetworkEntropologist/netbox-proxmox-ingester
cd netbox-proxmox-ingester/sample-implementation
python -m venv venv
source venv/bin/activate
pip install -r sample_requirements.txt
./sample_implementation.py
 ```

## High level process flow
At a hight level, the process flow is as follows:

1. Gather some basic information, including:
    - Proxmox host details.
    - Proxmox user with read access to the REST API.
    - Pin mode to use. See below for more information on this.
2. Perform API call to Proxmox to get a list of clusters and nodes.
3. Iterate through the list of nodes, retrieving a list of VMs for each node.
4. For each VM, the following information is retrieved from Proxmox:
    - Name
    - Memory
    - CPU
    - Host node
    - Running status
    - Agent status
5. If the agent is installed on the VM, the following information is also retrieved:
    - Network configuration, including OS-level NIC name and assigned IP Addresses.
    - Disk configuration.
6. Confirm if the user is happy to proceed with the ingestion.
7. Validate that nodes exist as NetBox devices.
8. Validate if the *Proxmox* cluster type exists. It will be created if it does not.
9. Validate if the clusters exist as NetBox Virtualisation Clusters. If not these will be created.
10. Create each VM, along with its associated objects.

### Virtual Network Configuration
Please note that as of NetBox version 4.2, MAC Addresses are now a separate object. This script 
will automatically check the version of NetBox running, and will ingest MAC Addresses accordingly.

### Virtual Disk Configuration
Please note that prior to Netbox version 3.7, Virtual Disks were simply a field on the VM object, 
and not a separate object type. This means that currently this script only supports NetBox 
version 3.7 and higher.

## Assumptions and exclusions
As this is simply a PoC, it is assumed that a number of associated NetBox objects/entities already 
exist:

- Nodes exist as NetBox devices.
- IP Address prefixes and subnets.
- The cluster type defaults to "Proxmox".

## General notes

### Pin mode
Pin mode is used to determine if a VM should be "pinned" or associated to a specific NetBox object 
when ingested. The options are:

- Node: The VM will be associated with a specific Proxmox node.
- Cluster: The VM will be assicated with a specific cluster.
- Neither (default): The VM will not be associated with either a node or cluster. 
