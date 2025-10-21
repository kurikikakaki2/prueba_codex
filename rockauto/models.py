"""Data models used by the RockAuto scraper."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class Category:
    """Represents a RockAuto category entry."""

    id: str
    name: str
    url: str
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Product:
    """Represents a product listed inside a category."""

    brand: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    details_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
