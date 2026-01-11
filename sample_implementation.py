
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

pin_vms_to_node = False

# Blank data trees
proxmox_tree = {
    'data' : []
    }
netbox_tree = {
    'data' : []
    }

current_node = ''
current_vm = 0

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
        return _info
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
        _vm_network = proxmox_api.nodes(node_name).qemu(vm_id).agent.get(
            'network-get-interfaces')
        return _vm_network['result']
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving disks for VM {vm_id} on node {node_name}: {e}")

def extract_vm_disks(vm_config: dict) -> list:
    """
    Extract and return a list of VM disks.
    
    Args:
        vm_config (dict): The VM config to examine.

    Returns:
        list: List of dicts containing VM disk information
    """

    _disks = []

    # Iterate through the provided dict and find only storage devices
    for key, value in vm_config.items():
        _disk = {}
        if (key.startswith('ide') or key.startswith('scsi')) and not key.startswith('scsihw') : # Indicates a storage device
            _size = int(str(value).split('size=')[1][:-1]) * 1024 # Size in MB
            _disk[key] = _size
            _disks.append(_disk)
    
    return _disks

def extract_vnics(vm_config: dict, node: str, vm: int ) -> list:
    """
    Compile a list of vNICs connected to the VM

    Args:
        vm_config (dict): The VM config to examine.

    Returns:
        list: List of dicts containing VM vNIC information.
    """

    _vnics = []

    _vm_network_config = get_vm_network(proxmox_api=proxmox_api, 
                                        node_name=node,
                                        vm_id=vm)

    # Iterate through the provided dict and find only vNICs
    for key, value in vm_config.items():
        _vnic = {}

        if key.startswith('net'): # Indicates a NIC
            # Start by extracting the MAC
            _vnic['mac'] = str(value).split('=')[1].split(',')[0]

            # Now find that MAC in the network config
            for vnic in _vm_network_config:

                if vnic['hardware-address'] == str(_vnic['mac']).lower():
                    _vnic['name'] = vnic['name']
                    _vnic['ips'] = extract_ip_details(vnic=_vnic['name'],
                                                vm_network=_vm_network_config)
                    
                    _vnics.append(_vnic)

    return _vnics

def extract_ip_details(vnic: str, vm_network: list) -> list:
    """Extract the IP Address details for this vNIC"""

    _ip_details = []

    # TODO: Tweak the IP Address finding logic to make it actually bloody work!

    # Iterate through the provided list to find the specified vNIC
    for nic in vm_network:
        # First find the section relating to this MAC.
        if nic['name'] == vnic:
            # Now extract the IP Address information
            for ip_address in nic['ip-addresses']:
                _ip_address = {}
                _ip_address['family'] = ip_address['ip-address-type']
                _ip_address['address'] = f'{ip_address["ip-address"]}/{ip_address["prefix"]}'

                _ip_details.append(_ip_address)
        
    return _ip_details

def convert_tree_to_netbox():
    """Convert the Proxmox tree to NetBox"""

    ...

def start_ingestion():
    """Start the NetBox ingestion process"""
    ...

# === Helper methods end here ===


# === Main implementation starts here ===

hostname_input = input(f'Proxmox Hostname [{hostname}]: ')
if hostname_input:
    hostname = hostname_input

username_input = input(f'Username [{username}]: ')
if username_input:
    username = username_input

password = getpass.getpass('Password: ')

pin_vms_input = input('Pin VMs to node? [y/N] ').lower()
match pin_vms_input:
    case 'y':
        pin_vms_to_node = True
    case 'n':
        pin_vms_to_node = False
    case _:
        print('Invalid input, defaulting to No.')


proxmox_api = ProxmoxAPI(hostname, 
                         user=username, 
                         password=password, 
                         verify_ssl=False)

# First we need to get a list of PVE nodes
_nodes_list = []
_nodes_list = get_proxmox_nodes(proxmox_api)

# Now, iterate through this list
for node in _nodes_list:
    current_node = node['node']

    # Start by adding the required information from each node to the tree
    _node_data = {}
    _node_data['name'] = node['node']
    _node_data['status'] = node['status']
    
    # For each node, get a list of VMs
    _node_vms = get_node_vms(proxmox_api=proxmox_api,
                             node_name=node['node'])
    
    # For each VM, get the filesystem config
    for vm in _node_vms:
        current_vm = vm['vmid']

        _vm_config = get_vm_config(proxmox_api=proxmox_api,
                                     node_name=node['node'],
                                     vm_id=vm['vmid'])
        
        print(f'Now processing VM ID {vm["vmid"]} with name {_vm_config["name"]} on node {node["node"]}')

        # Add the required base information for each VM
        _vm_data = {}
        _vm_data['name'] = _vm_config['name']
        _vm_data['ram'] = int(_vm_config['memory'])
        _vm_data['cpu'] = int(_vm_config['cores']) * int(_vm_config['sockets'])
        
        # Now add the disks. These are only available if the agent is installed
        if 'agent' in _vm_config:
            _vm_data['disks'] = extract_vm_disks(vm_config=_vm_config)

            # Now get the network information
            _vm_data['network'] = extract_vnics(vm_config=_vm_config,
                                                node=node['node'],
                                                vm=vm['vmid'])

        proxmox_tree['data'].append(_vm_data)

print('The following VM data was discovered:')
print(json.dumps(proxmox_tree))

ingest_to_netbox = input('Do you want to ingest this into NetBox? [y/N] ').lower()
if ingest_to_netbox == 'y':

    
    ...