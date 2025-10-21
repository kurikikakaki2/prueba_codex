"""FastAPI application exposing the RockAuto scraper."""

from __future__ import annotations

from typing import List, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query

from rockauto import Category, Product, RockAutoScraper

app = FastAPI(title="RockAuto Catalog API", version="0.1.0")


def get_scraper() -> RockAutoScraper:
    return RockAutoScraper()


@app.get(
    "/catalog/{year}/{make}/{model}/{engine}/categories",
    response_model=List[Category],
    summary="List available categories for a vehicle",
)
def list_categories(
    year: int,
    make: str,
    model: str,
    engine: str,
    scraper: RockAutoScraper = Depends(get_scraper),
) -> List[Category]:
    try:
        categories = scraper.get_categories(year=year, make=make, model=model, engine=engine)
    except httpx.HTTPError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        scraper.close()
    return categories


@app.get(
    "/catalog/{year}/{make}/{model}/{engine}/categories/{category_id}/products",
    response_model=List[Product],
    summary="List RockAuto products inside a category",
)
def list_products(
    year: int,
    make: str,
    model: str,
    engine: str,
    category_id: str,
    category_url: Optional[str] = Query(
        default=None,
        description=(
            "Optional absolute URL to the category page. If omitted the scraper will"
            " build one from the provided identifiers."
        ),
    ),
    scraper: RockAutoScraper = Depends(get_scraper),
) -> List[Product]:
    try:
        products = scraper.get_products(
            year=year,
            make=make,
            model=model,
            engine=engine,
            category_id=category_id,
            category_url=category_url,
        )
    except httpx.HTTPError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        scraper.close()
    return products
