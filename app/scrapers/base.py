from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ScrapeResult:
    price: float = 0.0
    currency: str = "USD"
    product_name: str = ""
    source_url: str = ""
    marketplace: str = ""
    confidence: float = 0.0


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, url: str, query: str) -> list[ScrapeResult]:
        ...
