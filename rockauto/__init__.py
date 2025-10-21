"""RockAuto scraping utilities."""

from .models import Category, Product

try:  # pragma: no cover - optional dependency guard for unit tests
    from .scraper import RockAutoScraper
except ModuleNotFoundError:  # pragma: no cover - makes parsers usable without httpx installed
    RockAutoScraper = None  # type: ignore[assignment]

__all__ = ["Category", "Product", "RockAutoScraper"]
