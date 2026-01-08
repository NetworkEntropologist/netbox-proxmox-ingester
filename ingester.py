
from proxmoxer import ProxmoxAPI

import json

def get_proxmox_nodes(host: str,
                      user: str,
                      password: str,
                      verify_ssl: bool = True):
    """
    Retrieve a list of Proxmox VE nodes from the specified host.

    Args:
        host (str): The host address.
        user (str): Username that has API access.
        password (str): Password for your API user.
        verify_ssl (bool): Whether to verify SSL certificates. Defaults to True.
    """

    if not host:
        raise ValueError('Host cannot be empty.')

    if not user:
        raise ValueError('User cannot be empty.')

    if not password:
        raise ValueError('Password cannot be empty.')

    try:
        proxmox = ProxmoxAPI(host, user=user, password=password, verify_ssl=verify_ssl)
        nodes = proxmox.nodes.get()
        return nodes
    except ConnectionError as e:
        print(f"Connection error occurred: {e}")
        return None

def get_proxmox_vms(host: str,
                     user: str,
                     password: str,
                     node: str,
                     verify_ssl: bool = True):
    """
    Retrieve a list of Proxmox VE virtual machines from the specified host.

    Args:
        host (str): The host address.
        user (str): Username that has API access.
        password (str): Password for your API user.
        verify_ssl (bool): Whether to verify SSL certificates. Defaults to True.
    """

    if not host:
        raise ValueError('Host cannot be empty.')

    if not user:
        raise ValueError('User cannot be empty.')

    if not password:
        raise ValueError('Password cannot be empty.')

    try:
        proxmox = ProxmoxAPI(host, user=user, password=password, verify_ssl=verify_ssl)
        vms = proxmox.nodes(node).qemu.get()
        return vms
    except ConnectionError as e:
        print(f"Connection error occurred: {e}")
        return None
