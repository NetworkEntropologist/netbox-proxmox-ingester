
from proxmox.nodes import ProxmoxNode
from proxmox.vms import ProxmoxVM

_proxmox_node = ProxmoxNode(hostname = 'proxmox.hbnet.co.za',
                            node = 'proxmox',
                            user = 'root@pam',
                            password = 'L011ip0p2!',
                            verify_ssl = False)

print()
