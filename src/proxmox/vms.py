
from nodes import ProxmoxNode

from enum import Enum
import json

class VMStatus(Enum):
    """Enumeration for Proxmox VE VM statuses"""
    RUNNING = "running"
    STOPPED = "stopped"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"

class ProxmoxVM():
    """A Proxmox VE Virtual Machine"""

    @property
    def proxmox_node(self) -> ProxmoxNode:
        """Get the ProxmoxNode instance associated with this VM."""
        return self._proxmox_node
    
    @property
    def vmid(self) -> int:
        """Get the VM ID of this Proxmox VE Virtual Machine."""
        return self._vmid

    def __init__(self,
                 proxmox_node: ProxmoxNode,
                 vm_json: dict):

        self._proxmox_node = proxmox_node
        self._vmid = int(vm_json['vmid'])
        self._name = str(vm_json['name'])
        self._status = VMStatus(vm_json['status']).name
        self._maxmemory = int(vm_json['maxmem']) / (1024 * 1024)  # Convert to MB
        self._memory = int(vm_json['mem']) / (1024 * 1024)
        
