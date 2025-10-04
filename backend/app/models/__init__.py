# Database models
# app/models/__init__.py

# Import glavnih modela
from .user import User
from .image import Image
from .machine import Machine
from .session import Session  # ako imaš model za sesije
from .target import Target    # ako imaš target model

# Dodaj sve ostale modele ovde
# from .other_model import OtherModel

# Napravi __all__ za lakši import
__all__ = [
    "User",
    "Image",
    "Machine",
    "Session",
    "Target",
    # dodaj ostale modele ovde
]

