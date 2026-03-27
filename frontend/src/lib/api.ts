import { useQuery } from "@tanstack/react-query";
import type { Shop, Sale, ShopCategory, ShopsResponse, SalesResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API client
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Shop queries
interface UseShopsParams {
  categories?: ShopCategory[];
  hasSale?: boolean;
  neighborhood?: string;
  minRating?: number;
  search?: string;
  limit?: number;
  offset?: number;
}

export function useShops(params: UseShopsParams = {}) {
  return useQuery({
    queryKey: ["shops", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();

      if (params.categories?.length) {
        searchParams.set("categories", params.categories.join(","));
      }
      if (params.hasSale) {
        searchParams.set("has_sale", "true");
      }
      if (params.neighborhood) {
        searchParams.set("neighborhood", params.neighborhood);
      }
      if (params.minRating) {
        searchParams.set("min_rating", params.minRating.toString());
      }
      if (params.search) {
        searchParams.set("q", params.search);
      }
      if (params.limit) {
        searchParams.set("limit", params.limit.toString());
      }
      if (params.offset) {
        searchParams.set("offset", params.offset.toString());
      }

      const query = searchParams.toString();
      const data = await fetchApi<ShopsResponse>(`/shops${query ? `?${query}` : ""}`);
      return data.shops;
    },
  });
}

export function useShop(id: string) {
  return useQuery({
    queryKey: ["shop", id],
    queryFn: () => fetchApi<Shop>(`/shops/${id}`),
    enabled: !!id,
  });
}

// Sale queries
interface UseSalesParams {
  shopId?: string;
  activeOnly?: boolean;
  limit?: number;
}

export function useSales(params: UseSalesParams = {}) {
  return useQuery({
    queryKey: ["sales", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();

      if (params.shopId) {
        searchParams.set("shop_id", params.shopId);
      }
      if (params.activeOnly) {
        searchParams.set("active_only", "true");
      }
      if (params.limit) {
        searchParams.set("limit", params.limit.toString());
      }

      const query = searchParams.toString();
      const data = await fetchApi<SalesResponse>(`/sales${query ? `?${query}` : ""}`);
      return data.sales;
    },
  });
}

export function useActiveSales() {
  return useSales({ activeOnly: true, limit: 50 });
}

// Neighborhoods
export function useNeighborhoods() {
  return useQuery({
    queryKey: ["neighborhoods"],
    queryFn: () => fetchApi<string[]>("/neighborhoods"),
  });
}

// Search
export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () => fetchApi<Shop[]>(`/search?q=${encodeURIComponent(query)}`),
    enabled: query.length >= 2,
  });
}
