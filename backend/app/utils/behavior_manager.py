"""
Behavior Manager
Manages job behaviors and their configurations
"""

from typing import Dict, Any, List, Optional, Tuple


class BehaviorManager:
    """Manages job behaviors and their metadata"""
    
    # Behavior definitions with metadata
    BEHAVIORS = {
        'machine_action': {
            'name': 'Machine Action',
            'description': 'Execute power actions on machines (power on, power off, restart, shutdown)',
            'fields': [
                {
                    'name': 'action',
                    'type': 'select',
                    'label': 'Action',
                    'required': True,
                    'options': [
                        {'value': 'power_on', 'label': 'Power On'},
                        {'value': 'power_off', 'label': 'Power Off'},
                        {'value': 'restart', 'label': 'Restart'},
                        {'value': 'shutdown', 'label': 'Shutdown'}
                    ]
                },
                {
                    'name': 'machine_ids',
                    'type': 'multiselect',
                    'label': 'Target Machines',
                    'required': True,
                    'options': []  # Will be populated from machines API
                }
            ]
        },
        'boot_state': {
            'name': 'Boot State',
            'description': 'Set boot state for machines',
            'fields': [
                {
                    'name': 'boot_state',
                    'type': 'select',
                    'label': 'Boot State',
                    'required': True,
                    'options': [
                        {'value': 'pxe', 'label': 'PXE Boot'},
                        {'value': 'local', 'label': 'Local Boot'},
                        {'value': 'image', 'label': 'Boot from Image'}
                    ]
                },
                {
                    'name': 'machine_ids',
                    'type': 'multiselect',
                    'label': 'Target Machines',
                    'required': True,
                    'options': []
                }
            ]
        },
        'snapshot': {
            'name': 'Snapshot',
            'description': 'Create snapshot of an image',
            'fields': [
                {
                    'name': 'image_id',
                    'type': 'select',
                    'label': 'Image',
                    'required': True,
                    'options': []
                },
                {
                    'name': 'machine_id',
                    'type': 'select',
                    'label': 'Machine (optional)',
                    'required': False,
                    'options': []
                },
                {
                    'name': 'description',
                    'type': 'textarea',
                    'label': 'Description',
                    'required': False
                }
            ]
        },
        'script': {
            'name': 'Script',
            'description': 'Execute a script',
            'fields': [
                {
                    'name': 'script_path',
                    'type': 'text',
                    'label': 'Script Path',
                    'required': True
                },
                {
                    'name': 'arguments',
                    'type': 'text',
                    'label': 'Arguments',
                    'required': False
                }
            ]
        },
        'trim': {
            'name': 'TRIM',
            'description': 'Execute TRIM operation on storage',
            'fields': [
                {
                    'name': 'array_id',
                    'type': 'select',
                    'label': 'Storage Array',
                    'required': True,
                    'options': []
                }
            ]
        },
        'backup': {
            'name': 'Backup',
            'description': 'Backup images',
            'fields': [
                {
                    'name': 'image_ids',
                    'type': 'multiselect',
                    'label': 'Images',
                    'required': True,
                    'options': []
                },
                {
                    'name': 'backup_type',
                    'type': 'select',
                    'label': 'Backup Type',
                    'required': True,
                    'options': [
                        {'value': 'local', 'label': 'Local Backup'},
                        {'value': 'remote', 'label': 'Remote Backup'}
                    ]
                },
                {
                    'name': 'backup_path',
                    'type': 'text',
                    'label': 'Backup Path',
                    'required': True
                }
            ]
        }
    }
    
    @classmethod
    def get_behaviors(cls) -> List[Dict[str, Any]]:
        """Get list of all available behaviors"""
        return [
            {
                'type': behavior_type,
                **metadata
            }
            for behavior_type, metadata in cls.BEHAVIORS.items()
        ]
    
    @classmethod
    def get_behavior(cls, behavior_type: str) -> Optional[Dict[str, Any]]:
        """Get behavior metadata by type"""
        if behavior_type in cls.BEHAVIORS:
            return {
                'type': behavior_type,
                **cls.BEHAVIORS[behavior_type]
            }
        return None
    
    @classmethod
    def validate_behavior_data(cls, behavior_type: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate behavior data against behavior definition"""
        behavior = cls.get_behavior(behavior_type)
        if not behavior:
            return False, f"Unknown behavior type: {behavior_type}"
        
        # Check required fields
        for field in behavior.get('fields', []):
            if field.get('required', False):
                field_name = field.get('name')
                if field_name not in data or not data[field_name]:
                    return False, f"Missing required field: {field.get('label', field_name)}"
        
        return True, None




