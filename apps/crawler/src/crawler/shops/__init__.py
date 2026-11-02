from crawler.shops.base import ShopAdapter
from crawler.shops.goldenchamps import GoldenChampsAdapter

# 새 어댑터는 여기에 등록한다
ADAPTERS: dict[str, type[ShopAdapter]] = {
    GoldenChampsAdapter.name: GoldenChampsAdapter,
}

__all__ = ["ADAPTERS", "ShopAdapter"]
