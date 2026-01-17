"""
Copyright 2026 The Network Entropologist

https://github.com/NetworkEntropologist

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""

from proxmoxer import ProxmoxAPI

import pynetbox

from enum import Enum

import json
import getpass

# === Global values and defaults start here ===

proxmox_host: str = 'proxmox.hbnet.co.za'
proxmox_username: str = 'api@pve'
netbox_host: str = 'https://dev.netbox.hbnet.co.za'
# Generally speaking, it is bad security practice to store these values in 
# code. These are placed here purely to make testing quicker and easier. 
# These can be safely removed, as this example will prompt the user for 
# these values at runtime anyways.

proxmox_password: str = ''
netbox_api_token: str = ''
# Very important to note that these values are not set here for security 
# reasons. The user will be prompted for these values at runtime in this 
# example. In a real production environment, these values should be stored 
# securely, such as in environment variables or in a secrets manager.

netbox_cluster_type = {
    'name' : 'Proxmox',
    'slug' : 'proxmox'
}
# This is the default NetBox cluster type information, but the user is given
# an opportunity to override this later. If this cluster type does not exist
# it will be created during ingestion.

# Default is to not pin VMs to nothing
vm_pin_method: str = 'e'

# Blank data tree
data_tree = {
    'pin_mode' : 'e', # Default pin mode is 'n[e]ither'
    'cluster': {},
    'netbox_cluster_type' : {},
    'nodes' : [],
    'vms' : [],
}

netbox_api = pynetbox.api(url='localhost',
                          token='000')

netbox_version = ()

# === Global values and defaults end here ===

# === Helper methods start here ===

def get_proxmox_overrides():
    """Get the default override values from the user"""
    global proxmox_host, proxmox_username, proxmox_password, vm_pin_method

    proxmox_host_input = input(f'Proxmox host [{proxmox_host}]: ')
    if proxmox_host_input:
        proxmox_host = proxmox_host_input

    username_input = input(f'Proxmox username [{proxmox_username}]: ')
    if username_input:
        proxmox_username = username_input

    proxmox_password = getpass.getpass('Password: ')

    vm_pin_method = input('Pin VMs to [n]ode, [c]luster or n[E]ither? ').lower()
    if vm_pin_method not in ['n','c', 'e']:
        print('Invalid input, defaulting to Neither.')
        vm_pin_method = 'e'

def get_netbox_overrides():
    """Get the NetBox override values"""
    global netbox_host, netbox_api_token, netbox_api

    netbox_host_input = input(f'NetBox host [{netbox_host}]: ')
    if netbox_host_input:
        netbox_host = netbox_host_input

    netbox_api_token = getpass.getpass('NetBox API Token: ')

    netbox_api = pynetbox.api(url= netbox_host,
                              token=netbox_api_token)

    cluster_type_name_input = input(f'NetBox cluster type name [{netbox_cluster_type["name"]}]: ')
    cluster_type_slug_input = input(f'NetBox cluster type slug [{netbox_cluster_type["slug"]}]: ')
    if cluster_type_name_input:
        netbox_cluster_type['name'] = cluster_type_name_input
    if cluster_type_slug_input:
        netbox_cluster_type['slug'] = cluster_type_slug_input

    data_tree['netbox_cluster_type'] = netbox_cluster_type

def populate_proxmox_cluster():
    """Return a list of Proxmox Clusters"""

    _raw_clusters = [] # Initialise an empty list
    try:
        _raw_clusters = proxmox_api('cluster/status').get()
    except ConnectionError as e:
        raise ConnectionError(f'Connection error occurred: {e}')
    
    # Setup an empty dict
    _cluster_members = []
    # Now iterate through this list and build a list of clusters and their respective nodes
    for item in _raw_clusters:
        if item['type'] == 'cluster': # Add a new cluster to the tree
            _cluster = {
                'name' : item['name'],
                'id' : item['id'],
                'type' : item['type'],
                'nodes' : item['nodes'] 
            }
            data_tree['cluster'] = _cluster
        if item['type'] == 'node': # Add a new node to the tree
            _node = {
                'node' : item['name'],
                'id' : item['id'],
                'type' : item['type'],
            }
            if item['online'] == 1:
                _node['status'] = 'online'
            else:
                _node['status'] = 'unknown'
            data_tree['nodes'].append(_node)

def populate_proxmox_nodes():
    """
    Get a list of Proxmox nodes.
    
    Returns:
        list: A list of Proxmox nodes.
    """
    try:
        _raw_nodes = proxmox_api.nodes.get()
    except ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    
    data_tree['nodes'] = _raw_nodes

def get_node_vms(node_name: str) -> list:
    """
    Get a list of VMs on the specified Proxmox node.

    Args:
        node_name (str): The name of the Proxmox node.
    
    Returns:
        list: A list of VMs on the specified node.
    """

    try:
        _raw_vms = proxmox_api.nodes(node_name).qemu.get()
        return _raw_vms
    except ConnectionError as e:
        raise ConnectionError(f"Error retrieving VMs for node {node_name}: {e}")

def get_vm_config(node_name: str, vm_id: int) -> dict:
    """
    Get the configuration of the specified VM. Please note that this is just 
    the basic config information as directly visible from Proxmox, and does 
    not include any additional information such as disk/volume config, network 
    interface names, IP Addresses, etc.

    Args:
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

def get_vm_fs(node_name: str, vm_id: int) -> dict:
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

def get_vm_network(node_name: str, vm_id: int):
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

def get_netbox_device_id(device_name: str) -> int:
    """Get the object ID for a NetBox Device"""
    global netbox_api

    try:
        netbox_device = netbox_api.dcim.devices.get(name=device_name)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0
    
    return netbox_device.id # type: ignore

def get_netbox_version() -> tuple:
    """Fetch the NetBox version"""

    try:
        version = netbox_api.status()['netbox-version']
    except ConnectionError as e:
        print(f'Error connection to NetBox API: {e}')

    major, minor, *_ = map(int, version.split('.'))

    return (major,minor)

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

    _vm_network_config = get_vm_network(node_name=node,
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

def start_ingestion():
    """Start the NetBox ingestion process"""

    # First we want to get the NetBox overrides and values
    get_netbox_overrides()

    # Now we need to check the NetBox version
    netbox_version = get_netbox_version()

    # Now we need to validate that the nodes exist as NetBox devices
    # Only execute this if we chose to pin the VM to a node
    if data_tree['pin_mode'] == 'n':
        print('Validating Proxmox nodes exist in NetBox')
        if not validate_nodes():
            return
    
    # The next steps are only executed if we chose to pin the VM to a cluster
    if data_tree['pin_mode'] == 'c':
        # Validate the cluster type specified
        print(f'Validating specified cluster type')
        if not validate_cluster_type():
            return
        
        # Validate that the cluster exists
        print(f'Validating cluster exists')
        if not validate_cluster():
            return
    
    # And finally, create the VMs
    print(f'Processing VMs')
    process_vms()

def validate_nodes() -> bool:
    """Validate all Proxmox nodes exist as NetBox devices"""
    global netbox_api

    invalid_nodes = []

    # Iterate the data tree and check each node exists
    i = 0 # Instantiate a simple index counter
    for node in data_tree['nodes']:
        print(f'Validating node {node["node"]}')

        try:
            device = netbox_api.dcim.devices.filter(name='proxmox')
        except ConnectionError as e:
            print(f'Error connecting to NetBox API: {e}')
            return False
        
        if not device:
            print(f'Node {node["node"]} does not exist in NetBox')
            invalid_nodes.append(node['node'])
        else:
            print(f'Setting NetBox device ID {device.id} to node in data tree')
            data_tree['nodes'][i]['netbox_id'] = device.id

        i += 1 # Remember to advance the index
    
    # If even one node does not exist, fail the entire process
    if len(invalid_nodes) != 0:
        print('The following invalid nodes were found:')
        print(invalid_nodes)
        print('Processing cannot continue until this has been resolved')
        return False

    return True # Return True at this point, because if we reach here, all nodes are valid

def validate_cluster_type() -> bool:
    """Validate that the cluster type exists in NetBox"""
    global netbox_api

    api_endpoint = netbox_api.virtualization.cluster_types

    try:    
        cluster_type = api_endpoint.get(name=data_tree['netbox_cluster_type']['name'])
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return False

    if not cluster_type:
        print(f'Cluster type ({data_tree["netbox_cluster_type"]["name"]}) does not exist in NetBox.')
        # Let's create the cluster type
        create_cluster_type()
    
    # Update the cluster type ID to the data tree
    else:
        data_tree['netbox_cluster_type']['netbox_id'] = cluster_type.id
    
    return True

def validate_cluster() -> bool:
    """Validate that the cluster exists in NetBox"""
    global netbox_api
    
    try:
        netbox_cluster = netbox_api.virtualization.clusters.get(
            name=data_tree['cluster']['name'])
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return False
    
    # If the cluster does not exist, as the user if they want to create it
    if not netbox_cluster: 
        print(f'NetBox cluster {data_tree["cluster"]["name"]} not found.')
        if input(f'Do you wish to create this automatically? [Y/n]').lower() == 'y':
            if create_cluster():
                return True # Cluster was just created
        
        print(f'Processing cannot continue if the cluster type does not exist.')
        return False # Cluster does not exist and user declined to create it
    
    # And finally, simply get the cluster ID, since if we reach this point, we know it exists
    data_tree['cluster']['netbox_id'] = netbox_cluster.id
    
    return True # Cluster does indeed exist

def validate_vm(vm_name: str) -> bool:
    """Validate if a VM exists in NetBox"""

    try:
        vm_results = netbox_api.virtualization.virtual_machines.filter(
            name=vm_name)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return True # Returning true for a connection error

    if len(vm_results) == 0:
        return False # VM does not exist
    
    return True # VM exists

def validate_ip(ip_address: str) -> int:
    """
    Check if an IP Address exists

    Args:
        ip_address (str): IP Address to validate
    
    Returns:
        int: Object ID if address exists, 0 if not
    """

    # Check if the address exists
    try:
        results = netbox_api.ipam.ip_addresses.get(address=ip_address)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0
    
    if results:
        return results['id']
    
    return 0

def create_cluster_type() -> bool:
    """Create new cluster type"""
    global netbox_api

    api_endpoint = netbox_api.virtualization.cluster_types

    print(f'Creating new Cluster Type {data_tree["netbox_cluster_type"]["name"]}')

    try:
        cluster_type = api_endpoint.create(name=data_tree["netbox_cluster_type"]["name"],
                                           slug=data_tree["netbox_cluster_type"]["slug"],
                                           description='Created by Proxmox ingester')
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return False # False means an error

    data_tree["netbox_cluster_type"]["netbox_id"] = cluster_type.id

    return True

def create_cluster() -> bool:
    """Create the required NetBox Virtualization Cluster object"""
    global netbox_api

    # Create the new cluster
    try:
        netbox_cluster = netbox_api.virtualization.clusters.create(
            name=data_tree['cluster']['name'],
            type=data_tree["netbox_cluster_type"]["netbox_id"],
            status='active',
            description='Created by Proxmox Ingester'
            )
    except ConnectionError as e:
        print(f'Error connecting to NetBox API {e}')
        return False

    # Set the new cluster ID
    data_tree['cluster']['id'] = netbox_cluster.id

    return True

def process_vms():
    """Process all VMs in the data tree"""

    # Iterate through the data tree and process each VM
    for vm in data_tree['vms']:
        print(f'Validating VM {vm["name"]}')

        # First check ig the VM exists and skip if required
        if validate_vm(vm_name=vm['name']):
            print(f'VM {vm["name"]} exists. Skipping.')
        
        # THe VM does not exist, so create it
        else:
            print(f'Creating VM {vm["name"]}')
            vm_id = create_vm(vm_details=vm)
            if vm_id == 0:
                print(f'Error!')

def create_vm(vm_details: dict) -> int:
    """Create a new NetBox VM"""
    global netbox_api

    vm_cluster = 0
    vm_node = 0
    new_vm_config = {'name' : vm_details['name'],
                     'vcpus' : vm_details['cpu'],
                     'memory' : vm_details['ram']
                     }

    # Let's quickly register an alias for the entire API endpoint
    # This simply shortens line lengths a bit further down
    api_endpoint = netbox_api.virtualization.virtual_machines

    # Now we need to set some values based on the selected pin mode
    match data_tree['pin_mode']:
        case 'c': # Pin the VM to the cluster
            print(f'Pinning VM to cluster {data_tree["cluster"]["name"]}')
            new_vm_config['cluster'] = data_tree['cluster']['netbox_id']
        case 'n': # Pin the VM to the node
            print(f'Pinning VM to node {vm_details["node"]}')
            new_vm_config['device'] = get_netbox_device_id(device_name=vm_details['node'])
        case 'e': # Do not pin the VM
            print(f'VM is unpinned')

    # Check and set the VM status to be NetBox compatible
    if vm_details['status'] == 'running':
        new_vm_config['status'] = 'active'
    else:
        new_vm_config['status'] = 'offline'

    # And now, let's create a VM!
    # First we need to actually create the VM itself
    try:
        vm_results = api_endpoint.create(new_vm_config)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0 # A return of 0 means an error occurred
    
    vm_id: int = vm_results.id # type: ignore
    print(f'VM {vm_details["name"]} created with ID {vm_id}')
    
    # Next we create vNICs and assign them to the VM
    if 'network' in vm_details:
        for vnic in vm_details['network']:
            vnic_id = create_vnic(name=vnic['name'], mac=vnic['mac'], vm_id=vm_id)

        # And now we need to create an IP Address and assign it to the vNIC
            for ip in vnic['ips']:
                create_ip(ip_address=ip['address'], interface_id=vnic_id)

    # Next, create the virtual disk
    if 'disks' in vm_details:
        for disk in vm_details['disks']:
            for disk_name, disk_size in disk.items():
                create_disk(name=disk_name, vm_id=vm_id, size=disk_size)
                print(f'Created disk {disk_name} of size {disk_size} MB for VM ID {vm_id}')
    

    return vm_id # There was some or other error

def create_vnic(name: str, mac: str, vm_id: int) -> int:
    """
    Create a new vNIC in NetBox
    
    Args:
        name (str): The vNIC name
        mac (str): The vNIC MAC Address
        vm_id (int): The VM NetBox ID
    
    Returns:
        int: The created vNIC ID
    """

    # First check/create MAC object ID
    mac_id = create_mac(mac_address=mac)

    try:
        results = netbox_api.virtualization.interfaces.create(virtual_machine=vm_id,
                                                            name=name,
                                                            primary_mac_address=mac_id)
        
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0
    
    return results['id'] 

def create_mac(mac_address: str) -> int:
    """
    Create a new MAC Address
    
    Args:
        mac_address (str): The MAC Address to create
    
    Returns:
        int: The created MAC Address ID
    """

    # First check if this MAC Address exists
    try:
        results = netbox_api.dcim.mac_addresses.get(mac_address=mac_address)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0

    if results:
        # Return the object ID
        return results['id']
    
    # Now, add a new MAC Address
    try:
        results = netbox_api.dcim.mac_addresses.create(mac_address=mac_address)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0

    # And return the object ID
    return results['id']

def create_ip(ip_address: str, interface_id: int):
    """
    Create a new IP address
    """

    # TODO: Add IP Address creation logic

    # Validate the IP does not exist yet
    ip_id = validate_ip(ip_address=ip_address)

    # If it does exist, return the object ID
    if ip_id != 0:
        print(f'IP Address {ip_address} already exists with ID {ip_id}')
        return ip_id
    
    # Now create an IP Address and return the object ID
    try:
        results = netbox_api.ipam.ip_addresses.create(address=ip_address,
                                                      assigned_object_type='virtualization.vminterface',
                                                    assigned_object_id=interface_id,
                                                    status='active')
        return results['id']
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0


    return 0 # There was an error

def create_disk(name: str, vm_id: int, size: int) -> int:
    """
    Create a new Disk in NetBox

    Args:
        name (str): The disk name
        vm_id (int): The VM NetBox ID
        size (int): The disk size in MB

    Returns:
        int: The created Disk ID
    """

    try:
        results = netbox_api.virtualization.virtual_disks.create(virtual_machine=vm_id,
                                                        name=name,
                                                        size=size)
    except ConnectionError as e:
        print(f'Error connecting to NetBox API: {e}')
        return 0
    
    return results['id']

# === Helper methods end here ===


# === Main implementation starts here ===

current_node = ''
current_vm = 0

get_proxmox_overrides()

proxmox_api = ProxmoxAPI(proxmox_host, 
                         user=proxmox_username, 
                         password=proxmox_password, 
                         verify_ssl=False)

_cluster_members = {}
_nodes_list = []
if vm_pin_method == 'c':
    data_tree['pin_mode'] = vm_pin_method
    populate_proxmox_cluster()
else:
    populate_proxmox_nodes()

# Now, iterate through this list
for node in data_tree['nodes']:
    current_node = node['node']

    # Start by adding the required information from each node to the tree
    _node_data = {}
    _node_data['name'] = node['node']
    _node_data['status'] = node['status']
    
    # For each node, get a list of VMs
    _node_vms = get_node_vms(node['node'])
    
    # For each VM, get the filesystem config
    for vm in _node_vms:
        current_vm = vm['vmid']

        _vm_config = get_vm_config(node_name=node['node'],
                                     vm_id=vm['vmid'])
        
        print(f'Now processing VM ID {vm["vmid"]} with name {_vm_config["name"]} on node {node["node"]}')

        # Add the required base information for each VM
        _vm_data = {}
        _vm_data['name'] = _vm_config['name']
        _vm_data['ram'] = int(_vm_config['memory'])
        _vm_data['cpu'] = int(_vm_config['cores']) * int(_vm_config['sockets'])
        _vm_data['node'] = current_node
        _vm_data['status'] = vm['status']
        
        # Now add the disks. These are only available if the agent is installed
        if 'agent' in _vm_config:
            _vm_data['disks'] = extract_vm_disks(vm_config=_vm_config)

            # Now get the network information
            _vm_data['network'] = extract_vnics(vm_config=_vm_config,
                                                node=node['node'],
                                                vm=vm['vmid'])

        data_tree['vms'].append(_vm_data)

print('The following VM data was discovered:')
print(json.dumps(data_tree, indent=2))

ingest_to_netbox = input('Do you want to ingest this into NetBox? [y/N] ').lower()
if ingest_to_netbox == 'y':
    start_ingestion()
