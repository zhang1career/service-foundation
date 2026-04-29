from __future__ import annotations

from enum import IntEnum

from common.dict_catalog import register_dict_code


@register_dict_code("cms_content_status")
class ContentStatus(IntEnum):
    DRAFT = 0
    PUBLISHED = 1

    def label(self) -> str:
        return {ContentStatus.DRAFT: "draft", ContentStatus.PUBLISHED: "published"}[self]

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [{"k": m.label(), "v": str(m.value)} for m in cls]


@register_dict_code("cms_product_stock_status")
class ProductStockStatus(IntEnum):
    UNKNOWN = 0
    IN_STOCK = 1
    OUT_OF_STOCK = 2

    def label(self) -> str:
        return {
            ProductStockStatus.UNKNOWN: "unknown",
            ProductStockStatus.IN_STOCK: "in_stock",
            ProductStockStatus.OUT_OF_STOCK: "out_of_stock",
        }[self]

    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [{"k": m.label(), "v": str(m.value)} for m in cls]
