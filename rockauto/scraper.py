"""High level scraper for RockAuto."""

from __future__ import annotations

import logging
import re
from typing import List, Optional
from urllib.parse import urlencode, urljoin

import httpx

from .models import Category, Product
from .parsers import parse_categories, parse_products

LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}


class RockAutoScraper:
    """Fetches categories and product listings directly from RockAuto."""

    def __init__(
        self,
        base_url: str = "https://www.rockauto.com",
        *,
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        merged_headers = dict(DEFAULT_HEADERS)
        if headers:
            merged_headers.update(headers)
        self._client = client or httpx.Client(base_url=self.base_url, timeout=timeout, headers=merged_headers)

    @staticmethod
    def _normalise_segment(value: str) -> str:
        cleaned = value.strip().lower()
        cleaned = cleaned.replace("/", " ")
        cleaned = re.sub(r"[^a-z0-9]+", "+", cleaned)
        cleaned = cleaned.strip("+")
        return cleaned

    def build_catalog_path(
        self,
        year: int | str,
        make: str,
        model: str,
        engine: Optional[str] = None,
    ) -> str:
        """Builds the relative catalog path used by RockAuto."""

        segments: List[str] = [
            self._normalise_segment(make),
            str(year),
            self._normalise_segment(model),
        ]
        if engine:
            segments.append(self._normalise_segment(engine))
        path = "/en/catalog/" + ",".join(segments)
        return path

    def get_categories(
        self,
        *,
        year: int | str,
        make: str,
        model: str,
        engine: Optional[str],
    ) -> List[Category]:
        """Return the categories available for the given vehicle."""

        path = self.build_catalog_path(year, make, model, engine)
        url = urljoin(self.base_url, path)
        LOGGER.debug("Fetching category page %s", url)
        response = self._client.get(url)
        response.raise_for_status()
        categories = parse_categories(response.text, url)
        if not categories:
            LOGGER.warning("No categories parsed for %s", url)
        return categories

    def get_products(
        self,
        *,
        year: int | str,
        make: str,
        model: str,
        engine: Optional[str],
        category_id: Optional[str] = None,
        category_url: Optional[str] = None,
        extra_query_params: Optional[dict[str, str]] = None,
    ) -> List[Product]:
        """Return the list of products for a category.

        ``category_url`` takes precedence. When only ``category_id`` is provided we
        append it as ``pt`` query parameter which is how RockAuto links its catalog
        pages.
        """

        if not category_url and not category_id:
            raise ValueError("Either category_url or category_id must be provided.")

        if category_url:
            url = category_url
        else:
            path = self.build_catalog_path(year, make, model, engine)
            query = {"pt": category_id}
            if extra_query_params:
                query.update(extra_query_params)
            url = urljoin(self.base_url, path)
            url = f"{url}?{urlencode(query)}"

        LOGGER.debug("Fetching product page %s", url)
        response = self._client.get(url)
        response.raise_for_status()
        products = parse_products(response.text, url)
        return products

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RockAutoScraper":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()
