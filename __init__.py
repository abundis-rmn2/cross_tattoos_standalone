# Cross Tattoos Standalone module
from config.settings import Config
from core.data_loader import DataLoader
from core.text_processor import TextProcessor
from core.constants import BODY_LOCATIONS, TATTOO_CATEGORIES

__version__ = "1.0.0"
__all__ = [
    'Config',
    'DataLoader', 
    'TextProcessor',
    'BODY_LOCATIONS',
    'TATTOO_CATEGORIES'
]
