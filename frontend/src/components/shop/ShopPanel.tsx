"use client";

import { X, MapPin, Clock, Phone, Globe, Instagram, Star, Percent, ExternalLink } from "lucide-react";
import { clsx } from "clsx";
import type { Shop } from "@/types";
import { CATEGORIES } from "@/types";
import { format } from "date-fns";

interface ShopPanelProps {
  shop: Shop | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ShopPanel({ shop, isOpen, onClose }: ShopPanelProps) {
  if (!shop) return null;

  const categoryColors = shop.categories.map(
    (catId) => CATEGORIES.find((c) => c.id === catId)?.color || "#666"
  );

  return (
    <div
      className={clsx(
        "absolute top-0 right-0 h-full w-96 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-10 overflow-hidden",
        isOpen ? "translate-x-0" : "translate-x-full"
      )}
    >
      {/* Header with image */}
      <div className="relative h-48 bg-gray-200">
        {shop.photos?.[0] ? (
          <img
            src={shop.photos[0]}
            alt={shop.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-amber-100 to-amber-200">
            <span className="text-6xl">🏪</span>
          </div>
        )}

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-2 bg-white/90 hover:bg-white rounded-full shadow-md transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Active sale badge */}
        {shop.activeSale && (
          <div className="sale-badge absolute bottom-3 left-3 px-3 py-1.5 bg-red-500 text-white rounded-full text-sm font-semibold flex items-center gap-1.5 shadow-lg">
            <Percent className="w-4 h-4" />
            {shop.activeSale.discountPercent
              ? `${shop.activeSale.discountPercent}% OFF`
              : "SALE"}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4 overflow-y-auto h-[calc(100%-12rem)]">
        {/* Title and rating */}
        <div className="mb-3">
          <h2 className="text-xl font-bold text-gray-900 mb-1">{shop.name}</h2>
          <div className="flex items-center gap-3 text-sm">
            {shop.rating && (
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                <span className="font-medium">{shop.rating.toFixed(1)}</span>
                {shop.reviewCount && (
                  <span className="text-gray-500">({shop.reviewCount})</span>
                )}
              </div>
            )}
            {shop.priceLevel && (
              <span className="text-gray-600">
                {"$".repeat(shop.priceLevel)}
              </span>
            )}
          </div>
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {shop.categories.map((catId, idx) => (
            <span
              key={catId}
              className="px-2 py-0.5 rounded-full text-xs font-medium text-white"
              style={{ backgroundColor: categoryColors[idx] }}
            >
              {CATEGORIES.find((c) => c.id === catId)?.name}
            </span>
          ))}
        </div>

        {/* Active sale details */}
        {shop.activeSale && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="font-semibold text-red-800 mb-1">
              {shop.activeSale.title}
            </h3>
            {shop.activeSale.description && (
              <p className="text-sm text-red-700 mb-2">
                {shop.activeSale.description}
              </p>
            )}
            <div className="flex items-center justify-between text-xs text-red-600">
              <span>
                via {shop.activeSale.source}
              </span>
              {shop.activeSale.endDate && (
                <span>
                  Ends {format(new Date(shop.activeSale.endDate), "MMM d")}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Description */}
        {shop.description && (
          <p className="text-sm text-gray-600 mb-4">{shop.description}</p>
        )}

        {/* Info */}
        <div className="space-y-3 mb-4">
          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-gray-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm text-gray-900">{shop.address}</p>
              <p className="text-xs text-gray-500">{shop.neighborhood}</p>
            </div>
          </div>

          {shop.phone && (
            <a
              href={`tel:${shop.phone}`}
              className="flex items-center gap-3 text-sm text-gray-900 hover:text-amber-600 transition-colors"
            >
              <Phone className="w-5 h-5 text-gray-400" />
              {shop.phone}
            </a>
          )}

          {shop.hours && (
            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-gray-400 mt-0.5" />
              <div className="text-sm">
                <p className="text-gray-900">Today&apos;s Hours</p>
                <p className="text-gray-500">
                  {shop.hours[
                    Object.keys(shop.hours)[
                      new Date().getDay() === 0 ? 6 : new Date().getDay() - 1
                    ] as keyof typeof shop.hours
                  ] || "Closed"}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Links */}
        <div className="flex gap-2">
          {shop.website && (
            <a
              href={shop.website}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-gray-700 transition-colors"
            >
              <Globe className="w-4 h-4" />
              Website
              <ExternalLink className="w-3 h-3" />
            </a>
          )}

          {shop.instagram && (
            <a
              href={`https://instagram.com/${shop.instagram}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-sm text-white transition-colors"
            >
              <Instagram className="w-4 h-4" />
              @{shop.instagram}
            </a>
          )}
        </div>

        {/* Recent sales history */}
        {shop.recentSales && shop.recentSales.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">
              Recent Sales
            </h3>
            <div className="space-y-2">
              {shop.recentSales.slice(0, 3).map((sale) => (
                <div
                  key={sale.id}
                  className="p-2 bg-gray-50 rounded-lg text-sm"
                >
                  <p className="font-medium text-gray-900">{sale.title}</p>
                  <p className="text-xs text-gray-500">
                    {format(new Date(sale.detectedAt), "MMM d, yyyy")} via{" "}
                    {sale.source}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
