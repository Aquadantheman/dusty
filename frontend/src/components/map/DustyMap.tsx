"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import mapboxgl from "mapbox-gl";
import type { Shop, ShopCategory } from "@/types";
import { CATEGORIES } from "@/types";
import { useShops } from "@/lib/api";

// Set Mapbox token
if (typeof window !== "undefined") {
  mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";
}

interface DustyMapProps {
  selectedShop: Shop | null;
  onShopSelect: (shop: Shop) => void;
  activeCategories: ShopCategory[];
  showSalesOnly: boolean;
}

// NYC default view
const NYC_CENTER: [number, number] = [-74.006, 40.7128];
const NYC_ZOOM = 12;

export function DustyMap({
  selectedShop,
  onShopSelect,
  activeCategories,
  showSalesOnly,
}: DustyMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<Map<string, mapboxgl.Marker>>(new Map());
  const [isLoaded, setIsLoaded] = useState(false);

  // Fetch shops
  const { data: shops = [] } = useShops({
    categories: activeCategories.length > 0 ? activeCategories : undefined,
    hasSale: showSalesOnly || undefined,
  });

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: NYC_CENTER,
      zoom: NYC_ZOOM,
      pitch: 0,
      bearing: 0,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), "bottom-right");

    // Add geolocation
    map.current.addControl(
      new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: false,
        showUserHeading: false,
      }),
      "bottom-right"
    );

    map.current.on("load", () => {
      setIsLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Create marker element
  const createMarkerElement = useCallback((shop: Shop): HTMLDivElement => {
    const el = document.createElement("div");
    el.className = "shop-marker";

    // Get primary category color
    const primaryCategory = shop.categories[0];
    const categoryInfo = CATEGORIES.find((c) => c.id === primaryCategory);
    const color = categoryInfo?.color || "#666";

    // Check if shop has active sale
    const hasSale = !!shop.activeSale;

    el.innerHTML = `
      <div class="relative cursor-pointer transform hover:scale-110 transition-transform">
        <div
          class="w-8 h-8 rounded-full border-2 border-white shadow-lg flex items-center justify-center"
          style="background-color: ${color}"
        >
          <span class="text-white text-xs font-bold">
            ${shop.name.charAt(0).toUpperCase()}
          </span>
        </div>
        ${
          hasSale
            ? `<div class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-white flex items-center justify-center">
                <span class="text-white text-[8px] font-bold">%</span>
              </div>`
            : ""
        }
      </div>
    `;

    return el;
  }, []);

  // Update markers when shops change
  useEffect(() => {
    if (!map.current || !isLoaded) return;

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current.clear();

    // Add new markers
    shops.forEach((shop) => {
      const el = createMarkerElement(shop);

      el.addEventListener("click", () => {
        onShopSelect(shop);
      });

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([shop.lng, shop.lat])
        .addTo(map.current!);

      markersRef.current.set(shop.id, marker);
    });
  }, [shops, isLoaded, createMarkerElement, onShopSelect]);

  // Fly to selected shop
  useEffect(() => {
    if (!map.current || !selectedShop) return;

    map.current.flyTo({
      center: [selectedShop.lng, selectedShop.lat],
      zoom: 15,
      duration: 1000,
    });

    // Highlight selected marker
    markersRef.current.forEach((marker, id) => {
      const el = marker.getElement();
      if (id === selectedShop.id) {
        el.style.zIndex = "10";
        el.querySelector(".w-8")?.classList.add("ring-2", "ring-amber-400");
      } else {
        el.style.zIndex = "1";
        el.querySelector(".w-8")?.classList.remove("ring-2", "ring-amber-400");
      }
    });
  }, [selectedShop]);

  return (
    <div ref={mapContainer} className="map-container w-full h-full">
      {/* Loading indicator */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">Loading map...</span>
          </div>
        </div>
      )}

      {/* Shop count badge */}
      {isLoaded && shops.length > 0 && (
        <div className="absolute top-4 left-4 px-3 py-1.5 bg-white/90 backdrop-blur rounded-full shadow-md text-sm font-medium text-gray-700">
          {shops.length} shop{shops.length !== 1 ? "s" : ""} found
          {showSalesOnly && " with sales"}
        </div>
      )}
    </div>
  );
}
