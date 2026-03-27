"""
Sale/Event database model
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import enum


class SaleSource(str, enum.Enum):
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    FACEBOOK = "facebook"
    EMAIL = "email"
    MANUAL = "manual"


class Sale(Base):
    """Sale/promotional event model"""

    __tablename__ = "sales"

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("shops.id"), nullable=False, index=True)

    # Sale details
    title = Column(String, nullable=False)
    description = Column(String)
    discount_percent = Column(Integer)  # e.g., 20 for 20% off

    # Dates
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Source tracking
    source = Column(Enum(SaleSource), nullable=False)
    source_url = Column(String)
    source_post_id = Column(String)  # Instagram post ID, etc.

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Detection metadata
    detected_at = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=1.0)  # How confident we are this is a sale
    raw_text = Column(String)  # Original text that triggered detection

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shop = relationship("Shop", back_populates="sales")

    def __repr__(self):
        return f"<Sale {self.title} @ {self.shop_id}>"

    @property
    def is_expired(self) -> bool:
        """Check if sale has expired"""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date
