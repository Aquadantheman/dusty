"""
Shop database model
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import enum


class ShopCategory(str, enum.Enum):
    VINTAGE = "vintage"
    ANTIQUE = "antique"
    THRIFT = "thrift"
    CONSIGNMENT = "consignment"
    CLOTHING = "clothing"
    FURNITURE = "furniture"
    RECORDS = "records"


class Shop(Base):
    """Vintage/Antique shop model"""

    __tablename__ = "shops"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    address = Column(String, nullable=False)
    neighborhood = Column(String, index=True)
    city = Column(String, default="NYC")

    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Categories (stored as JSON array)
    categories = Column(JSON, default=list)

    # Details
    description = Column(String)
    phone = Column(String)
    website = Column(String)
    instagram = Column(String)
    hours = Column(JSON)  # {"monday": "10am-6pm", ...}

    # Ratings
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    price_level = Column(Integer)  # 1-4

    # Photos
    photos = Column(JSON, default=list)  # List of URLs

    # Data source tracking
    google_place_id = Column(String)
    yelp_id = Column(String)
    osm_id = Column(String)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime)

    # Relationships
    sales = relationship("Sale", back_populates="shop", lazy="selectin")

    def __repr__(self):
        return f"<Shop {self.name}>"

    @property
    def has_active_sale(self) -> bool:
        """Check if shop has any active sales"""
        return any(sale.is_active for sale in self.sales)

    @property
    def active_sale(self):
        """Get the most recent active sale"""
        active_sales = [s for s in self.sales if s.is_active]
        return active_sales[0] if active_sales else None
