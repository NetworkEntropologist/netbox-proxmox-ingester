
from proxmoxer import ProxmoxAPI

import json
import getpass

hostname = 'proxmox.hbnet.co.za'    # type: str
username = 'api@pve'                # type: str
# Generally speaking, it is bad security practice to store these values in 
# code. These are placed here purely to make testing quicker and easier. 
# These can be safely removed, as this example will prompt the user for 
# these values at runtime anyways.

# Very important to note that the password is not set here for security 
# reasons. The user will be prompted for the password at runtime in this 
# exaample. In a real production environment, these values should be stored 
# securely, such as in environment variables or in a secrets manager.

invalid_nodes = []

# Blank data trees
proxmox_tree = {
    'data' : []
    }
netbox_tree = {
    'data' : []
    }

_node_data = {}
# _node_data = {'name' : '', 'status' : '', 'vms' : ['name' : '', 'status' : '', 'fs' : [], 'network' : []]}


# === Helper methods start here ===

def get_proxmox_nodes(proxmox_api: ProxmoxAPI) -> list:
    """
    Get a list of Proxmox nodes.
    
    Args:
        proxmox_api (ProxmoxAPI): An instance of the Proxmox API class.
    
    Returns:
        list: A list of Proxmox nodes.
    """
    
    try:
        _raw_nodes = proxmox_api.nodes.get()
        return _raw_nodes
    except ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")

def get_node_vms(proxmox_api: ProxmoxAPI, node_name: str) -> list:
    """
    Get a list of VMs on the specified Proxmox node.

    Args:
        proxmox_api (ProxmoxAPI): An instance of the Proxmox API class.
        node_name (str): The name of the Proxmox node.
    
    Returns:
        list: A list of VMs on the specified node.
    """

    try:
        _raw_vms = proxmox_api.nodes(node_name).qemu.get()
        return _raw_vms
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving VMs for node {node_name}: {e}")

def get_vm_config(proxmox_api: ProxmoxAPI, node_name: str, vm_id: int) -> dict:
    """
    Get the configuration of the specified VM. Please note that this is just 
    the basic config information as directly visible from Proxmox, and does 
    not include any additional information such as disk/volume config, network 
    interface names, IP Addresses, etc.

    Args:
        proxmox_api (ProxmoxAPI): An instance of the Proxmox API class.
        node_name (str): The name of the Proxmox node.
        vm_id (int): The VM ID. This is NOT the same as the VM name!

    Returns:
        dict: The configuration of the specified VM.
    """

    try:
        _info = proxmox_api.nodes(node_name).qemu(vm_id).config.get()
        return _info['data']
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving info for VM " \
                              "{vm_id} on node {node_name}: {e}")

def get_vm_fs(proxmox_api: ProxmoxAPI, node_name: str, vm_id: int) -> dict:
    """
    Get the file system information for the specified VM. This uses the agent 
    functionality, so the agent absolutely needs to be installed and enabled 
    on the VM for this to work, as this information is not directly visible 
    from inside Proxmox.

    Args:
        proxmox_api (ProxmoxAPI): An instance of the Proxmox API class.
        node_name (str): The name of the Proxmox node.
        vm_id (int): The VM ID. This is NOT the same as the VM name!

    Returns:
        dict: The disk and volume information for the specified VM.
    """

    try:
        _disks = proxmox_api.nodes(node_name).qemu(vm_id).agent.get(
            'get-fsinfo')
        return _disks['data']
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving filesystem for VM {vm_id} " \
                              "on node {node_name}: {e}")

def get_vm_network(proxmox_api: ProxmoxAPI, node_name: str, vm_id: int):
    """
    Get the network information for the specified VM. This uses the agent 
    functionality, so the agent absolutely needs to be installed and enabled 
    on the VM for this to work, as this information is not directly visible 
    from inside Proxmox. 

    Args:
        proxmox_api (ProxmoxAPI): An instance of the Proxmox API class.
        node_name (str): The name of the Proxmox node.
        vm_id (int): The VM ID. This is NOT the same as the VM name!

    Returns:
        dict: The network information for the specified VM.

    """

    try:
        _vm_network = proxmox_api.nodes(node_name).qemu(vm_id).config.get(
            'network-get-interfaces')
        return _vm_network['data']
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving disks for VM {vm_id} on node {node_name}: {e}")

# === Helper methods end here ===


# === Main implementation starts here ===

hostname_input = input(f'Proxmox Hostname [{hostname}]: ')
if hostname_input:
    hostname = hostname_input

username_input = input(f'Username [{username}]: ')
if username_input:
    username = username_input

password = getpass.getpass('Password: ')

proxmox_api = ProxmoxAPI(hostname, 
                         user=username, 
                         password=password, 
                         verify_ssl=False)

# First we need to get a list of PVE nodes
_nodes_list = []
_nodes_list = get_proxmox_nodes(proxmox_api)

# Now, iterate through this list
for node in _nodes_list:
    # Start by adding the required information from each node to the tree
    
    netbox_tree['data'].append
    
    # For each node, get a list of VMs
    _node_vms = get_node_vms(proxmox_api=proxmox_api,
                             node_name=node['node'])
    
    # For each VM, get the filesystem config
    for vm in _node_vms:
        # Add each VM to the Proxmox tree under the node


        # For each VM, get the network information
            
            # Add the filesystem info for the VM to the Proxmox tree
            # Add the network info for the VM to the Proxmox tree
    

