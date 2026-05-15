from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

class ReportWriter(ABC):
    @classmethod
    @abstractmethod
    def print_header(cls, header: str, level: int = 1) -> str:
        pass
    
    @classmethod
    @abstractmethod
    def print_paragraph(cls, text: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def print_bold(cls, text: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def print_table(cls, df: pd.DataFrame) -> str:
        pass
    
    @classmethod
    @abstractmethod
    def print_list(cls, items: list[str], numbered: bool = False, inline: bool = False) -> str:
        pass
    
    @classmethod
    @abstractmethod
    def print_empty_line(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def print_image(cls, image_path: Path, alt_text: str = "") -> str:
        pass

    @classmethod
    @abstractmethod
    def print_link(cls, text: str, url: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_property_section_link(cls, property_id: int) -> str:
        """Return a link to the property section in the report based on the property ID."""
        pass

    @classmethod
    @abstractmethod
    def get_extension(cls) -> str:
        """Return the file extension associated with this report type (e.g., 'md' for Markdown)."""
        pass

    @classmethod
    @abstractmethod
    def initialize_report(cls, title: str) -> str:
        pass
    
    @classmethod
    @abstractmethod
    def finalize_report(cls) -> str:
        pass

# Registry to hold the value-to-class mapping
CLASS_REGISTRY = {}

def register_class(value):
    """Decorator factory that registers a class under a specific value."""
    def decorator(cls):
        CLASS_REGISTRY[value] = cls
        return cls  # Returns the class as-is while registering it
    return decorator

def get_class_by_value(value):
    """Utility to fetch the class based on the provided value."""
    if value not in CLASS_REGISTRY:
        raise ValueError(f"No report writer registered for value: {value}")
    return CLASS_REGISTRY.get(value)
