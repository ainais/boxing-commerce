from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class ScrapedProduct:
    shop: str
    shop_product_no: str
    name: str
    model_summary: str | None
    price: int
    list_price: int | None
    image_url: str
    product_url: str
    sold_out: bool
    category_no: int
    scraped_at: datetime

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["scraped_at"] = self.scraped_at.isoformat()
        return data
