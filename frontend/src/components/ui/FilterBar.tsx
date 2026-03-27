"use client";

import { clsx } from "clsx";
import {
  Clock,
  Gem,
  Tag,
  Sparkles,
  Shirt,
  Armchair,
  Disc,
  Percent,
} from "lucide-react";
import type { ShopCategory } from "@/types";
import { CATEGORIES } from "@/types";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Clock,
  Gem,
  Tag,
  Sparkles,
  Shirt,
  Armchair,
  Disc,
};

interface FilterBarProps {
  activeCategories: ShopCategory[];
  onToggleCategory: (category: ShopCategory) => void;
  showSalesOnly: boolean;
  onToggleSalesOnly: () => void;
}

export function FilterBar({
  activeCategories,
  onToggleCategory,
  showSalesOnly,
  onToggleSalesOnly,
}: FilterBarProps) {
  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
        {/* Sales filter */}
        <button
          onClick={onToggleSalesOnly}
          className={clsx(
            "category-pill flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all",
            showSalesOnly
              ? "bg-red-500 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          )}
        >
          <Percent className="w-4 h-4" />
          <span>Sales</span>
        </button>

        <div className="w-px h-6 bg-gray-300 mx-1" />

        {/* Category filters */}
        {CATEGORIES.map((category) => {
          const Icon = iconMap[category.icon];
          const isActive = activeCategories.includes(category.id);

          return (
            <button
              key={category.id}
              onClick={() => onToggleCategory(category.id)}
              className={clsx(
                "category-pill flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all",
                isActive
                  ? "text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              )}
              style={isActive ? { backgroundColor: category.color } : undefined}
            >
              {Icon && <Icon className="w-4 h-4" />}
              <span>{category.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
