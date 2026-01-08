
from proxmoxer import ProxmoxAPI

from vms import ProxmoxVM
import json



class ProxmoxNode():
    """Class representing a Proxmox VE node"""

    @property
    def hostname(self) -> str:
        """Get the hostname of the Proxmox VE node."""
        return self._hostname
    @property
    def node(self) -> str:
        """Get the node name of the Proxmox VE node."""
        return self._node
    @property
    def user(self) -> str:
        """Get the username used for authentication."""
        return self._user

    def __init__(self,
                 hostname: str,
                 node: str,
                 user: str,
                 password: str,
                 verify_ssl: bool = True):
        """Initialize ProxmoxNode with connection details."""

        self._hostname = hostname
        self._node = node
        self._user = user
        self._password = password
        self.verify_ssl = verify_ssl
        self._proxmox_node = ProxmoxAPI(hostname, user=user, password=password, verify_ssl=verify_ssl)

    def _get_vms(self):
        """Retrieve a list of VMs on this Proxmox VE node"""

        _vms = []
        _raw_vms = []

        try:
            _raw_vms = self._proxmox_node.nodes(self._node).qemu.get()
        except ConnectionError as e:
            print(f"Connection error occurred: {e}")

        if _raw_vms is None:
            return _vms

        for vm in _raw_vms:
            _vm = ProxmoxVM(
                proxmox_node=self,
                vmid=vm['vmid']
            )
            _vms.append(_vm)

        return _vms

def get_proxmox_nodes(host, user, password, verify_ssl=False):
    """
    Connects to a Proxmox VE server and retrieves a list of nodes.

    Args:
        host (str): The hostname or IP address of the Proxmox VE server.
        user (str): The username for authentication.
        password (str): The password for authentication.
        verify_ssl (bool): Whether to verify SSL certificates.
    """

    try:
        proxmox = ProxmoxAPI(host, user=user, password=password, verify_ssl=verify_ssl)
        nodes = proxmox.nodes.get()
        return nodes
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_node_vms(hostname: str, node: str, user: str, password: str, verify_ssl=False):
    """
    Retrieves a list of virtual machines on a specified Proxmox VE node.

    Args:
        hostname (str): The hostname or IP address of the Proxmox VE server.
        node (str): The name of the node to query.
        user (str): The username for authentication.
        password (str): The password for authentication.
        verify_ssl (bool): Whether to verify SSL certificates.
    """

    try:
        proxmox = ProxmoxAPI(hostname, user=user, password=password, verify_ssl=verify_ssl)
        vms = proxmox.nodes(node).qemu.get()
        return vms
    except Exception as e:
        print(f"An error occurred: {e}")
        return None 
    


