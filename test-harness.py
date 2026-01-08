
from proxmoxer import ProxmoxAPI

import json
import getpass

hostname = 'proxmox.hbnet.co.za'    # type: str
username = 'api@pve'                # type: str
# Generally speaking, it is bad security practice to store these values in code.
# These are placed here purely to make testing quicker and easier. These can be 
# safely removed, as there is provision further down in the code to input these 
# at runtime.

invalid_nodes = []

proxmox_tree = []
netbox_tree = []

def get_proxmox_nodes(proxmox_api: ProxmoxAPI):
    
    _nodes = []
    try:
        _nodes = proxmox_api.nodes.get()
        return _nodes
    except ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")

def get_node_vms(proxmox_api: ProxmoxAPI, node_name: str):

    try:
        vms = proxmox_api.nodes(node_name).qemu.get()
        return vms
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving VMs for node {node_name}: {e}")

def get_vm_info(proxmox_api: ProxmoxAPI, node_name: str, vm_id: int):

    try:
        _info = {}
        _info = proxmox_api.nodes(node_name).qemu(vm_id).config.get()
        return _info['data']
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving info for VM {vm_id} on node {node_name}: {e}")

def get_vm_disks(proxmox_api: ProxmoxAPI, node_name: str, vm_id: int):

    try:
        _disks = proxmox_api.nodes(node_name).qemu(vm_id).config.get()
        return _disks
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving disks for VM {vm_id} on node {node_name}: {e}")


hostname_input = input(f'Proxmox Hostname [{hostname}]: ')
if hostname_input:
    hostname = hostname_input

username_input = input(f'Username [{username}]: ')
if username_input:
    username = username_input

password = getpass.getpass('Password: ')

proxmox_api = ProxmoxAPI(hostname, user=username, password=password, verify_ssl=False)

# Get a list of proxmox nodes
_nodes_raw = []
_nodes_raw = get_proxmox_nodes(proxmox_api)

# Now let's iterate through each node to get some information
for node in _nodes_raw:
    _node = {}
    _node['name'] = node['node']
    _node['status'] = node['status']
    
    # Next we need to get the VM information for this node
    _vms = []
    _vms = get_node_vms(proxmox_api, node['node'])

    for vm in _vms:
        _vm = {}
        _vm['name'] = vm['name']
        _vm['id'] = vm['id']
        _vm_config = get_vm_info(proxmox_api, node['node'], vm['id'])
        _vm['memory'] = int(_vm_config['memory']) 
        _vm['sockets'] = int(_vm_config['sockets'])
        _vm['cores'] = int(_vm_config['cores'])
        _vm[]

    # Now iterate through each VM to get some information
    

