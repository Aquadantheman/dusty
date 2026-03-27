// Shop Categories
export type ShopCategory =
  | "vintage"
  | "antique"
  | "thrift"
  | "consignment"
  | "clothing"
  | "furniture"
  | "records";

// Shop data structure
export interface Shop {
  id: string;
  name: string;
  address: string;
  neighborhood: string;
  lat: number;
  lng: number;
  categories: ShopCategory[];
  description?: string;
  phone?: string;
  website?: string;
  instagram?: string;
  hours?: ShopHours;
  rating?: number;
  reviewCount?: number;
  priceLevel?: 1 | 2 | 3 | 4; // $ to $$$$
  photos?: string[];
  activeSale?: Sale;
  recentSales?: Sale[];
  lastUpdated: string;
}

export interface ShopHours {
  monday?: string;
  tuesday?: string;
  wednesday?: string;
  thursday?: string;
  friday?: string;
  saturday?: string;
  sunday?: string;
}

// Sale/Event data
export interface Sale {
  id: string;
  shopId: string;
  title: string;
  description?: string;
  discountPercent?: number;
  startDate?: string;
  endDate?: string;
  source: SaleSource;
  sourceUrl?: string;
  detectedAt: string;
  isActive: boolean;
}

export type SaleSource = "instagram" | "website" | "facebook" | "email" | "manual";

// Map view state
export interface MapViewState {
  center: [number, number];
  zoom: number;
  pitch?: number;
  bearing?: number;
}

// API response types
export interface ShopsResponse {
  shops: Shop[];
  total: number;
  hasMore: boolean;
}

export interface SalesResponse {
  sales: Sale[];
  total: number;
}

// Filter state
export interface FilterState {
  categories: ShopCategory[];
  showSalesOnly: boolean;
  neighborhood?: string;
  priceLevel?: number[];
  minRating?: number;
  searchQuery?: string;
}

// Category metadata
export interface CategoryInfo {
  id: ShopCategory;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export const CATEGORIES: CategoryInfo[] = [
  {
    id: "vintage",
    name: "Vintage",
    description: "Clothing and items from past eras",
    icon: "Clock",
    color: "#8B4513",
  },
  {
    id: "antique",
    name: "Antique",
    description: "Items 100+ years old, collectibles",
    icon: "Gem",
    color: "#DAA520",
  },
  {
    id: "thrift",
    name: "Thrift",
    description: "Secondhand goods at budget prices",
    icon: "Tag",
    color: "#228B22",
  },
  {
    id: "consignment",
    name: "Consignment",
    description: "Curated luxury and designer items",
    icon: "Sparkles",
    color: "#9932CC",
  },
  {
    id: "clothing",
    name: "Clothing",
    description: "Vintage fashion boutiques",
    icon: "Shirt",
    color: "#DC143C",
  },
  {
    id: "furniture",
    name: "Furniture",
    description: "Antique and vintage furniture",
    icon: "Armchair",
    color: "#2F4F4F",
  },
  {
    id: "records",
    name: "Records",
    description: "Vinyl and vintage audio",
    icon: "Disc",
    color: "#1E90FF",
  },
];
