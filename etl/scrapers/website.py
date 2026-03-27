"""
Website scraper for detecting sales and events
Checks shop websites for sale announcements, banners, etc.
"""

import httpx
import re
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


@dataclass
class WebsiteSale:
    """Sale detected from a website"""
    title: str
    description: Optional[str]
    discount_percent: Optional[int]
    url: str
    detected_at: datetime
    confidence: float
    raw_text: str


class WebsiteScraper:
    """Scrape shop websites for sale announcements"""

    # Keywords that indicate a sale section/page
    SALE_URL_KEYWORDS = [
        "sale", "sales", "clearance", "deals", "offers",
        "discount", "markdown", "special", "promo",
    ]

    # Sale indicators in page content
    SALE_PATTERNS = [
        (r"(\d{1,2})\s*%\s*off", "percentage", 0.5),
        (r"\b(sale|sales)\b", "sale_keyword", 0.2),
        (r"\b(clearance)\b", "clearance", 0.4),
        (r"\b(up\s*to\s*\d{1,2}\s*%)", "up_to_percent", 0.4),
        (r"\b(free\s*shipping)", "free_shipping", 0.1),
        (r"\b(limited\s*time)", "limited", 0.3),
        (r"\b(ends?\s*soon)", "ending", 0.3),
        (r"\b(today\s*only)", "today", 0.4),
        (r"\b(extra\s*\d{1,2}\s*%\s*off)", "extra_off", 0.5),
        (r"\b(buy\s*one\s*get\s*one|bogo)", "bogo", 0.4),
    ]

    # Elements that often contain sale banners
    BANNER_SELECTORS = [
        ".sale-banner", ".promo-banner", ".announcement-bar",
        ".hero-banner", ".top-banner", "#announcement",
        "[class*='sale']", "[class*='promo']", "[class*='banner']",
        "header .announcement", ".site-header-banner",
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )

    async def check_website(self, url: str) -> List[WebsiteSale]:
        """
        Check a shop's website for sale announcements.
        Looks at the homepage and any linked sale pages.
        """

        sales = []

        try:
            # Fetch the homepage
            response = await self.client.get(url)

            if response.status_code != 200:
                print(f"Failed to fetch {url}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Check homepage for sale banners
            homepage_sales = self._extract_sales_from_page(soup, url)
            sales.extend(homepage_sales)

            # Find and check sale pages
            sale_links = self._find_sale_links(soup, url)

            for sale_url in sale_links[:3]:  # Limit to 3 sale pages
                try:
                    sale_response = await self.client.get(sale_url)
                    if sale_response.status_code == 200:
                        sale_soup = BeautifulSoup(sale_response.text, "html.parser")
                        page_sales = self._extract_sales_from_page(sale_soup, sale_url)
                        sales.extend(page_sales)
                except Exception as e:
                    print(f"Error fetching sale page {sale_url}: {e}")

                await asyncio.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"Error checking {url}: {e}")

        return sales

    def _find_sale_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find links to sale/clearance pages"""

        sale_links = []

        for link in soup.find_all("a", href=True):
            href = link.get("href", "").lower()
            text = link.get_text().lower()

            # Check if link URL or text indicates a sale page
            if any(kw in href for kw in self.SALE_URL_KEYWORDS) or \
               any(kw in text for kw in self.SALE_URL_KEYWORDS):

                full_url = urljoin(base_url, link["href"])

                # Only include internal links
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    if full_url not in sale_links:
                        sale_links.append(full_url)

        return sale_links

    def _extract_sales_from_page(
        self,
        soup: BeautifulSoup,
        page_url: str,
    ) -> List[WebsiteSale]:
        """Extract sale information from a page"""

        sales = []

        # Check banner elements
        for selector in self.BANNER_SELECTORS:
            try:
                for element in soup.select(selector):
                    text = element.get_text(strip=True)
                    if text and len(text) > 5:
                        sale = self._analyze_text(text, page_url)
                        if sale:
                            sales.append(sale)
            except Exception:
                continue

        # Check meta tags for promotional content
        for meta in soup.find_all("meta", {"name": ["description", "og:description"]}):
            content = meta.get("content", "")
            if content:
                sale = self._analyze_text(content, page_url)
                if sale:
                    sales.append(sale)

        # Check page title
        title_tag = soup.find("title")
        if title_tag:
            sale = self._analyze_text(title_tag.get_text(), page_url)
            if sale:
                sales.append(sale)

        # Check heading elements
        for heading in soup.find_all(["h1", "h2", "h3"]):
            text = heading.get_text(strip=True)
            if text:
                sale = self._analyze_text(text, page_url)
                if sale:
                    sales.append(sale)

        # Dedupe by title
        seen_titles = set()
        unique_sales = []
        for sale in sales:
            if sale.title not in seen_titles:
                seen_titles.add(sale.title)
                unique_sales.append(sale)

        return unique_sales

    def _analyze_text(self, text: str, url: str) -> Optional[WebsiteSale]:
        """Analyze text for sale indicators"""

        text_lower = text.lower()
        confidence = 0.0
        matches = []

        for pattern, pattern_type, weight in self.SALE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                matches.append((pattern_type, match.group()))
                confidence += weight

        if not matches or confidence < 0.3:
            return None

        confidence = min(confidence, 1.0)

        # Extract discount percentage
        discount_percent = None
        for pattern_type, match_text in matches:
            if pattern_type in ["percentage", "up_to_percent", "extra_off"]:
                percent_match = re.search(r"(\d{1,2})", match_text)
                if percent_match:
                    discount_percent = int(percent_match.group(1))
                    break

        # Generate title
        title = self._generate_title(matches, discount_percent)

        return WebsiteSale(
            title=title,
            description=text[:300] if len(text) > 300 else text,
            discount_percent=discount_percent,
            url=url,
            detected_at=datetime.utcnow(),
            confidence=confidence,
            raw_text=text,
        )

    def _generate_title(
        self,
        matches: List[tuple],
        discount_percent: Optional[int],
    ) -> str:
        """Generate a sale title"""

        for pattern_type, _ in matches:
            if pattern_type == "clearance":
                return "Clearance Sale"
            elif pattern_type == "bogo":
                return "Buy One Get One"

        if discount_percent:
            return f"{discount_percent}% Off Sale"

        return "Sale"

    async def close(self):
        await self.client.aclose()


import asyncio
