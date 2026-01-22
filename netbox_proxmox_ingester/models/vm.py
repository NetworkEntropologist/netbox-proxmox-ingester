
class VirtualMachine:
    """A class representing a virtual machine object."""

# === Start Public Properties ===



# === End Public Properties ===

    def __init__(self):
        """Initialize the Virtual Machine with default properties."""

        # VM Properties and default values
        _proxmox_id: int = 0
        _netbox_id: int = 0
        _name: str = ""
        _status: str = ""
        _cpus: int = 0
        _memory_mb: int = 0
        _disks: list = []
        _vnics: list = []
        _tags: list = []
        _cluster: str = ""
        _host: str = ""
        _template: bool = False


