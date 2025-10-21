"""Unit tests for the RockAuto HTML parsers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from rockauto.parsers import parse_categories, parse_products


CATEGORY_HTML = """
<html>
  <body>
    <div id="navcategories">
      <a href="/en/catalog/toyota,2010,camry,2.5l+l4,2020,brake+pad">Brake Pads</a>
      <a href="/en/catalog/toyota,2010,camry,2.5l+l4,2021,rotor">Brake Rotors</a>
      <a href="/en/catalog/toyota,2010,camry,2.5l+l4&pt=2020">Duplicate Example</a>
      <a href="/help/">Help Pages</a>
    </div>
  </body>
</html>
"""


PRODUCT_HTML = """
<html>
  <body>
    <table class="listing">
      <tr class="listingrow" data-partnumber="18A925A">
        <td class="listing-brand">ACDELCO</td>
        <td class="listing-description">Professional; Rear</td>
        <td class="listing-price">$45.79</td>
        <td><a href="/en/moreinfo.php?pk=12345">Info</a></td>
      </tr>
      <tr class="listingrow">
        <td class="listing-brand">CENTRIC</td>
        <td class="listing-description">Premium</td>
        <td class="listing-price">$39.10</td>
        <td><a href="/en/moreinfo.php?pk=67890">Info</a></td>
      </tr>
    </table>
  </body>
</html>
"""


def test_parse_categories_extracts_unique_entries() -> None:
    categories = parse_categories(CATEGORY_HTML, "https://www.rockauto.com/en/catalog/toyota,2010,camry,2.5l+l4")
    assert {c.id for c in categories} == {"2020", "2021"}
    assert categories[0].name == "Brake Pads"
    assert categories[0].url.startswith("https://www.rockauto.com/en/catalog/toyota")


def test_parse_products_extracts_core_fields() -> None:
    products = parse_products(PRODUCT_HTML, "https://www.rockauto.com/en/catalog/toyota,2010,camry,2.5l+l4")
    assert len(products) == 2
    first = products[0]
    assert first.brand == "ACDELCO"
    assert first.part_number == "18A925A"
    assert first.price == "$45.79"
    assert first.details_url.endswith("pk=12345")
