"""
Common serialization utilities for Pydantic models
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=BaseModel)


class ModelSerializer:
    """Utility class for model serialization"""
    
    @staticmethod
    def serialize_model(model: Any, response_class: Type[T]) -> T:
        """Serialize a SQLAlchemy model to Pydantic response model"""
        return response_class.model_validate(model)
    
    @staticmethod
    def serialize_model_list(models: List[Any], response_class: Type[T]) -> List[T]:
        """Serialize a list of SQLAlchemy models to Pydantic response models"""
        return [response_class.model_validate(model) for model in models]
    
    @staticmethod
    def serialize_dict(data: Dict[str, Any], response_class: Type[T]) -> T:
        """Serialize a dictionary to Pydantic response model"""
        return response_class.model_validate(data)


class DateTimeSerializer:
    """DateTime serialization utilities"""
    
    @staticmethod
    def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string"""
        if dt is None:
            return None
        return dt.isoformat()
    
    @staticmethod
    def serialize_datetime_list(dts: List[Optional[datetime]]) -> List[Optional[str]]:
        """Serialize list of datetimes to ISO format strings"""
        return [DateTimeSerializer.serialize_datetime(dt) for dt in dts]


class PaginationSerializer:
    """Pagination serialization utilities"""
    
    @staticmethod
    def create_pagination_response(
        items: List[Any],
        total: int,
        skip: int = 0,
        limit: int = 100,
        response_class: Type[T] = None
    ) -> Dict[str, Any]:
        """Create paginated response"""
        if response_class:
            serialized_items = ModelSerializer.serialize_model_list(items, response_class)
        else:
            serialized_items = items
        
        return {
            "items": serialized_items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + len(items) < total,
            "has_prev": skip > 0,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1
        }


class ErrorSerializer:
    """Error serialization utilities"""
    
    @staticmethod
    def serialize_validation_error(error: Exception) -> Dict[str, Any]:
        """Serialize validation error to standard format"""
        return {
            "error": "validation_error",
            "message": str(error),
            "type": type(error).__name__
        }
    
    @staticmethod
    def serialize_not_found_error(resource_type: str, resource_id: Any) -> Dict[str, Any]:
        """Serialize not found error"""
        return {
            "error": "not_found",
            "message": f"{resource_type} with id {resource_id} not found",
            "resource_type": resource_type,
            "resource_id": str(resource_id)
        }
    
    @staticmethod
    def serialize_permission_error(action: str, resource: str) -> Dict[str, Any]:
        """Serialize permission error"""
        return {
            "error": "permission_denied",
            "message": f"Permission denied for {action} on {resource}",
            "action": action,
            "resource": resource
        }


class StatsSerializer:
    """Statistics serialization utilities"""
    
    @staticmethod
    def serialize_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize statistics with proper formatting"""
        serialized = {}
        
        for key, value in stats.items():
            if isinstance(value, datetime):
                serialized[key] = DateTimeSerializer.serialize_datetime(value)
            elif isinstance(value, (int, float)):
                serialized[key] = value
            elif isinstance(value, str):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        
        return serialized
    
    @staticmethod
    def calculate_percentage(part: int, total: int) -> float:
        """Calculate percentage with proper handling of zero division"""
        if total == 0:
            return 0.0
        return round((part / total) * 100, 2)


class FileSerializer:
    """File-related serialization utilities"""
    
    @staticmethod
    def serialize_file_info(file_path: str, file_size: int) -> Dict[str, Any]:
        """Serialize file information"""
        return {
            "path": file_path,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "size_gb": round(file_size / (1024 * 1024 * 1024), 2)
        }
    
    @staticmethod
    def serialize_upload_progress(uploaded: int, total: int) -> Dict[str, Any]:
        """Serialize upload progress"""
        percentage = StatsSerializer.calculate_percentage(uploaded, total)
        return {
            "uploaded_bytes": uploaded,
            "total_bytes": total,
            "percentage": percentage,
            "is_complete": uploaded >= total
        }


class NetworkSerializer:
    """Network-related serialization utilities"""
    
    @staticmethod
    def serialize_network_info(ip: str, port: int, protocol: str = "tcp") -> Dict[str, Any]:
        """Serialize network connection info"""
        return {
            "ip_address": ip,
            "port": port,
            "protocol": protocol,
            "endpoint": f"{ip}:{port}"
        }
    
    @staticmethod
    def serialize_mac_address(mac: str) -> Dict[str, Any]:
        """Serialize MAC address with different formats"""
        # Remove separators for raw format
        raw_mac = mac.replace(':', '').replace('-', '')
        
        return {
            "standard": mac,  # Already in standard format
            "raw": raw_mac,
            "uppercase": mac.upper(),
            "lowercase": mac.lower()
        }


def create_response_model(
    data: Any,
    response_class: Type[T],
    include_metadata: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> Union[T, Dict[str, Any]]:
    """Create response model with optional metadata"""
    if isinstance(data, list):
        serialized_data = ModelSerializer.serialize_model_list(data, response_class)
    else:
        serialized_data = ModelSerializer.serialize_model(data, response_class)
    
    if include_metadata:
        return {
            "data": serialized_data,
            "metadata": metadata or {}
        }
    
    return serialized_data


def serialize_enum_value(enum_value: Any) -> str:
    """Serialize enum value to string"""
    if hasattr(enum_value, 'value'):
        return enum_value.value
    return str(enum_value)


def serialize_optional_enum(enum_value: Any) -> Optional[str]:
    """Serialize optional enum value to string"""
    if enum_value is None:
        return None
    return serialize_enum_value(enum_value)
