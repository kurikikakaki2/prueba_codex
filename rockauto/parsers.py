"""HTML parsing helpers for RockAuto pages without external dependencies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

from .models import Category, Product


@dataclass
class _PartialCategory:
    id: str
    name: str
    url: str
    parent_id: Optional[str] = None


def _normalise_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None


def _is_catalog_link(url: str) -> bool:
    """Return True when the URL points to a RockAuto catalog resource."""

    parsed = urlparse(url)
    if "/catalog/" in parsed.path:
        return True
    query = parse_qs(parsed.query)
    for key in ("pt", "parttype", "partType", "category"):
        if key in query:
            return True
    return False


def _extract_category_id_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("pt", "parttype", "partType", "category"):
        value = query.get(key)
        if value:
            return value[0]

    path_without_slash = parsed.path.rstrip("/")
    segments = path_without_slash.split(",") if "," in path_without_slash else path_without_slash.split("/")
    segments = [segment for segment in segments if segment]
    last_segment = segments[-1].strip() if segments else ""
    if last_segment and re.search(r"\d", last_segment) is None and len(segments) >= 2:
        last_segment = segments[-2].strip()
    if not last_segment:
        return None
    if not last_segment:
        return None

    digit_match = re.search(r"(\d{3,})", last_segment)
    if digit_match:
        return digit_match.group(1)

    slug = re.sub(r"[^a-z0-9]+", "-", last_segment.lower()).strip("-")
    return slug or None


class _CategoryHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.categories: List[_PartialCategory] = []
        self._current_href: Optional[str] = None
        self._buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if not href:
            return
        full_url = urljoin(self.base_url, href)
        if not _is_catalog_link(full_url):
            return
        identifier = _extract_category_id_from_url(full_url)
        if not identifier:
            return
        self._current_href = full_url
        self._buffer = []

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._current_href is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "a" and self._current_href is not None:
            name = _normalise_text("".join(self._buffer))
            if name:
                identifier = _extract_category_id_from_url(self._current_href)
                if identifier:
                    self.categories.append(
                        _PartialCategory(id=identifier, name=name, url=self._current_href)
                    )
            self._current_href = None
            self._buffer = []


def parse_categories(html: str, base_url: str) -> List[Category]:
    parser = _CategoryHTMLParser(base_url)
    parser.feed(html)
    unique: dict[str, _PartialCategory] = {}
    for category in parser.categories:
        unique.setdefault(category.id, category)
    return [Category(**cat.__dict__) for cat in unique.values()]


@dataclass
class _PartialProduct:
    brand: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    details_url: Optional[str] = None


class _ProductHTMLParser(HTMLParser):
    LISTING_ROW_CLASSES = {"listingrow", "listing-row", "listingRow"}

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.products: List[Product] = []
        self._current_row: Optional[_PartialProduct] = None
        self._current_field: Optional[str] = None
        self._buffer: List[str] = []
        self._row_stack: List[str] = []

    @staticmethod
    def _has_listing_class(attrs_dict: dict[str, str]) -> bool:
        class_attr = attrs_dict.get("class", "")
        classes = {item.strip() for item in class_attr.split()} if class_attr else set()
        return bool(_ProductHTMLParser.LISTING_ROW_CLASSES & classes)

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        attrs_dict = dict(attrs)

        if tag == "tr":
            if attrs_dict.get("data-partnumber") or self._has_listing_class(attrs_dict):
                self._current_row = _PartialProduct()
                self._current_row.part_number = attrs_dict.get("data-partnumber")
                self._row_stack.append("tr")
            return

        if self._current_row is None:
            return

        if tag == "td":
            class_attr = attrs_dict.get("class", "")
            classes = {item.strip() for item in class_attr.split()} if class_attr else set()
            field_map = {
                "listing-brand": "brand",
                "listing-mfr": "brand",
                "mfr": "brand",
                "brand": "brand",
                "listing-description": "description",
                "application": "description",
                "description": "description",
                "listing-price": "price",
                "price": "price",
                "partnumber": "part_number",
            }
            for cls in classes:
                if cls in field_map:
                    self._current_field = field_map[cls]
                    self._buffer = []
                    break
            else:
                self._current_field = None
                self._buffer = []
            return

        if tag == "a":
            href = attrs_dict.get("href")
            if href and self._current_row.details_url is None:
                if "moreinfo.php" in href or "catalog/" in href:
                    self._current_row.details_url = urljoin(self.base_url, href)
            part_number = attrs_dict.get("data-partnumber")
            if part_number and not self._current_row.part_number:
                self._current_row.part_number = part_number
            if self._current_field is None:
                # allow anchors to populate active field (e.g. part number)
                self._buffer = []
                self._current_field = "part_number"
            return

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._current_field is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "td" and self._current_field is not None and self._current_row is not None:
            value = _normalise_text("".join(self._buffer))
            if value:
                if self._current_field == "price":
                    price_match = re.search(r"\$\s*[0-9]+(?:[.,][0-9]{2})?", value)
                    value = price_match.group(0).replace(" ", "") if price_match else value
                setattr(self._current_row, self._current_field, value)
            self._current_field = None
            self._buffer = []
            return

        if tag == "a" and self._current_field == "part_number" and self._current_row is not None:
            value = _normalise_text("".join(self._buffer))
            if value:
                self._current_row.part_number = self._current_row.part_number or value
            self._buffer = []
            self._current_field = None
            return

        if tag == "tr" and self._current_row is not None:
            if self._row_stack:
                self._row_stack.pop()
            if not self._row_stack:
                if any(
                    [
                        self._current_row.brand,
                        self._current_row.part_number,
                        self._current_row.description,
                        self._current_row.price,
                    ]
                ):
                    self.products.append(Product(**self._current_row.__dict__))
                self._current_row = None
                self._current_field = None
                self._buffer = []


def parse_products(html: str, base_url: str) -> List[Product]:
    parser = _ProductHTMLParser(base_url)
    parser.feed(html)
    return parser.products
