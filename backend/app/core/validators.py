"""
Common validation utilities for Pydantic models
"""

import re
import ipaddress
from typing import Any, Optional
from pydantic import field_validator


class NetworkValidators:
    """Network-related validation utilities"""
    
    @staticmethod
    @field_validator('mac_address')
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validate and normalize MAC address format"""
        if not v:
            raise ValueError('MAC address cannot be empty')
            
        # Remove common separators and convert to standard format
        mac = re.sub(r'[:-]', '', v.upper())
        
        # Validate MAC address format
        if not re.match(r'^[0-9A-F]{12}$', mac):
            raise ValueError('Invalid MAC address format. Expected 12 hexadecimal characters')
        
        # Convert to standard format with colons
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    
    @staticmethod
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP address format"""
        if v is None:
            return v
            
        try:
            # Use ipaddress module for proper validation
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')
    
    @staticmethod
    @field_validator('ip_range')
    @classmethod
    def validate_ip_range(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP range format (CIDR)"""
        if v is None:
            return v
            
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError('Invalid IP range format. Use CIDR notation (e.g., 192.168.1.0/24)')


class StringValidators:
    """String validation utilities"""
    
    @staticmethod
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name field"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        
        if len(v.strip()) > 100:
            raise ValueError('Name cannot exceed 100 characters')
        
        return v.strip()
    
    @staticmethod
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description field"""
        if v is None:
            return v
        
        if len(v) > 500:
            raise ValueError('Description cannot exceed 500 characters')
        
        return v.strip() if v.strip() else None
    
    @staticmethod
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v: Optional[str]) -> Optional[str]:
        """Validate hostname format"""
        if v is None:
            return v
        
        if not v.strip():
            return None
        
        # Basic hostname validation
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', v):
            raise ValueError('Invalid hostname format')
        
        if len(v) > 253:
            raise ValueError('Hostname cannot exceed 253 characters')
        
        return v.lower().strip()


class NumericValidators:
    """Numeric validation utilities"""
    
    @staticmethod
    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number"""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @staticmethod
    @field_validator('size_bytes')
    @classmethod
    def validate_size_bytes(cls, v: int) -> int:
        """Validate size in bytes"""
        if v < 0:
            raise ValueError('Size cannot be negative')
        return v
    
    @staticmethod
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout value"""
        if v < 0:
            raise ValueError('Timeout cannot be negative')
        if v > 3600:  # 1 hour max
            raise ValueError('Timeout cannot exceed 3600 seconds')
        return v


class FileValidators:
    """File-related validation utilities"""
    
    @staticmethod
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename"""
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, v):
            raise ValueError('Filename contains invalid characters')
        
        if len(v) > 255:
            raise ValueError('Filename cannot exceed 255 characters')
        
        return v.strip()
    
    @staticmethod
    @field_validator('file_extension')
    @classmethod
    def validate_file_extension(cls, v: str) -> str:
        """Validate file extension"""
        if not v:
            raise ValueError('File extension cannot be empty')
        
        # Remove leading dot if present
        ext = v.lstrip('.')
        
        if not re.match(r'^[a-zA-Z0-9]+$', ext):
            raise ValueError('File extension contains invalid characters')
        
        if len(ext) > 10:
            raise ValueError('File extension cannot exceed 10 characters')
        
        return ext.lower()


def validate_positive_int(value: Any, field_name: str = "value") -> int:
    """Validate that a value is a positive integer"""
    if not isinstance(value, int):
        raise ValueError(f'{field_name} must be an integer')
    if value <= 0:
        raise ValueError(f'{field_name} must be positive')
    return value


def validate_non_negative_int(value: Any, field_name: str = "value") -> int:
    """Validate that a value is a non-negative integer"""
    if not isinstance(value, int):
        raise ValueError(f'{field_name} must be an integer')
    if value < 0:
        raise ValueError(f'{field_name} cannot be negative')
    return value


def validate_optional_string(value: Any, max_length: int = 255, field_name: str = "value") -> Optional[str]:
    """Validate optional string with length limit"""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValueError(f'{field_name} must be a string')
    
    value = value.strip()
    if not value:
        return None
    
    if len(value) > max_length:
        raise ValueError(f'{field_name} cannot exceed {max_length} characters')
    
    return value
