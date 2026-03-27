"""
Instagram scraper for detecting sales and events
Uses public API endpoints (no authentication required for public profiles)
"""

import httpx
import re
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class InstagramPost:
    """Parsed Instagram post"""
    post_id: str
    username: str
    caption: str
    timestamp: datetime
    image_url: Optional[str] = None
    post_url: Optional[str] = None
    likes: int = 0
    comments: int = 0


@dataclass
class DetectedSale:
    """A sale detected from social media"""
    title: str
    description: Optional[str]
    discount_percent: Optional[int]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    source: str
    source_url: str
    source_post_id: str
    raw_text: str
    confidence: float


class InstagramScraper:
    """Scrape Instagram profiles for sale announcements"""

    # Regex patterns for detecting sales
    SALE_PATTERNS = [
        # Percentage off
        (r"(\d{1,2})\s*%\s*off", "percentage"),
        (r"(\d{1,2})\s*percent\s*off", "percentage"),

        # Sale keywords
        (r"\b(sale|sales)\b", "sale_keyword"),
        (r"\b(clearance)\b", "clearance"),
        (r"\b(flash\s*sale)\b", "flash_sale"),
        (r"\b(sample\s*sale)\b", "sample_sale"),
        (r"\b(warehouse\s*sale)\b", "warehouse_sale"),
        (r"\b(moving\s*sale)\b", "moving_sale"),
        (r"\b(estate\s*sale)\b", "estate_sale"),
        (r"\b(closing\s*sale)\b", "closing_sale"),

        # Discount language
        (r"\b(discount|discounted)\b", "discount"),
        (r"\b(mark\s*down|markdown|marked\s*down)\b", "markdown"),
        (r"\b(price\s*cut|pricecut)\b", "price_cut"),
        (r"\b(reduced)\b", "reduced"),

        # Time-sensitive
        (r"\b(today\s*only)\b", "today_only"),
        (r"\b(this\s*weekend)\b", "weekend"),
        (r"\b(limited\s*time)\b", "limited_time"),
        (r"\b(last\s*chance)\b", "last_chance"),
        (r"\b(ends?\s*(today|tomorrow|sunday|monday|tuesday|wednesday|thursday|friday|saturday))\b", "end_date"),
    ]

    # Date patterns for extracting sale dates
    DATE_PATTERNS = [
        r"(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)",  # MM/DD or MM/DD/YY
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?)",  # "Jan 15"
        r"(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)",  # "15th of January"
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )

    async def get_recent_posts(
        self,
        username: str,
        limit: int = 12,
    ) -> List[InstagramPost]:
        """
        Get recent posts from a public Instagram profile.
        Uses the public web interface (no API key needed).
        """

        # Try to fetch the profile page
        url = f"https://www.instagram.com/{username}/"

        try:
            response = await self.client.get(url)

            if response.status_code != 200:
                print(f"Failed to fetch @{username}: {response.status_code}")
                return []

            # Extract JSON data from the page
            # Instagram embeds data in a script tag
            html = response.text

            # Look for the shared data JSON
            match = re.search(r'window\._sharedData\s*=\s*({.+?});</script>', html)
            if not match:
                # Try alternate pattern
                match = re.search(r'"PostPage":\s*\[({.+?})\]', html)

            if not match:
                print(f"Could not parse Instagram page for @{username}")
                return []

            # Parse posts from the data
            # This is a simplified version - real implementation would need
            # to handle Instagram's various data formats
            posts = self._extract_posts_from_html(html, username, limit)
            return posts

        except Exception as e:
            print(f"Error fetching @{username}: {e}")
            return []

    def _extract_posts_from_html(
        self,
        html: str,
        username: str,
        limit: int,
    ) -> List[InstagramPost]:
        """Extract post data from Instagram HTML"""

        posts = []

        # Find all post shortcodes in the page
        # This is a simplified extraction - Instagram's actual structure varies
        shortcode_pattern = r'"shortcode":"([A-Za-z0-9_-]+)"'
        caption_pattern = r'"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"([^"]+)"\}\}\]\}'

        shortcodes = re.findall(shortcode_pattern, html)
        captions = re.findall(caption_pattern, html)

        for i, shortcode in enumerate(shortcodes[:limit]):
            caption = captions[i] if i < len(captions) else ""

            # Unescape the caption
            caption = caption.encode().decode('unicode_escape')

            posts.append(InstagramPost(
                post_id=shortcode,
                username=username,
                caption=caption,
                timestamp=datetime.utcnow(),  # Would need to extract actual timestamp
                post_url=f"https://www.instagram.com/p/{shortcode}/",
            ))

        return posts

    def detect_sale(self, post: InstagramPost) -> Optional[DetectedSale]:
        """Analyze a post to detect if it's announcing a sale"""

        text = post.caption.lower()
        matches = []
        confidence = 0.0

        # Check for sale patterns
        for pattern, pattern_type in self.SALE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matches.append((pattern_type, match.group()))

                # Assign confidence based on pattern type
                if pattern_type == "percentage":
                    confidence += 0.4
                elif pattern_type in ["flash_sale", "sample_sale", "warehouse_sale", "estate_sale"]:
                    confidence += 0.5
                elif pattern_type == "sale_keyword":
                    confidence += 0.2
                elif pattern_type in ["today_only", "last_chance", "limited_time"]:
                    confidence += 0.3
                else:
                    confidence += 0.1

        # No sale indicators found
        if not matches:
            return None

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        # Only report if confidence is above threshold
        if confidence < 0.3:
            return None

        # Extract discount percentage if mentioned
        discount_percent = None
        for pattern_type, match_text in matches:
            if pattern_type == "percentage":
                discount_match = re.search(r"(\d{1,2})", match_text)
                if discount_match:
                    discount_percent = int(discount_match.group(1))
                    break

        # Generate title
        title = self._generate_sale_title(matches, discount_percent)

        return DetectedSale(
            title=title,
            description=post.caption[:200] if len(post.caption) > 200 else post.caption,
            discount_percent=discount_percent,
            start_date=None,  # Would need more sophisticated date extraction
            end_date=None,
            source="instagram",
            source_url=post.post_url or f"https://instagram.com/{post.username}",
            source_post_id=post.post_id,
            raw_text=post.caption,
            confidence=confidence,
        )

    def _generate_sale_title(
        self,
        matches: List[tuple],
        discount_percent: Optional[int],
    ) -> str:
        """Generate a sale title from detected patterns"""

        # Check for specific sale types
        for pattern_type, _ in matches:
            if pattern_type == "flash_sale":
                return "Flash Sale"
            elif pattern_type == "sample_sale":
                return "Sample Sale"
            elif pattern_type == "warehouse_sale":
                return "Warehouse Sale"
            elif pattern_type == "estate_sale":
                return "Estate Sale"
            elif pattern_type == "moving_sale":
                return "Moving Sale"
            elif pattern_type == "closing_sale":
                return "Closing Sale"
            elif pattern_type == "clearance":
                return "Clearance Sale"

        # Generic sale with discount
        if discount_percent:
            return f"{discount_percent}% Off Sale"

        return "Sale"

    async def scrape_shop(self, instagram_handle: str) -> List[DetectedSale]:
        """Scrape a shop's Instagram for sales"""

        # Remove @ if present
        username = instagram_handle.lstrip("@")

        posts = await self.get_recent_posts(username, limit=12)
        sales = []

        for post in posts:
            sale = self.detect_sale(post)
            if sale:
                sales.append(sale)

        return sales

    async def close(self):
        await self.client.aclose()
