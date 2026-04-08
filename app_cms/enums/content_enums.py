from __future__ import annotations

from enum import IntEnum


class ContentStatus(IntEnum):
    DRAFT = 0
    PUBLISHED = 1

    def label(self) -> str:
        return {ContentStatus.DRAFT: "draft", ContentStatus.PUBLISHED: "published"}[self]


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
