"use client";

import { useState } from "react";
import { DustyMap } from "@/components/map/DustyMap";
import { ShopPanel } from "@/components/shop/ShopPanel";
import { FilterBar } from "@/components/ui/FilterBar";
import { Header } from "@/components/ui/Header";
import type { Shop, ShopCategory } from "@/types";

export default function Home() {
  const [selectedShop, setSelectedShop] = useState<Shop | null>(null);
  const [activeCategories, setActiveCategories] = useState<ShopCategory[]>([]);
  const [showSalesOnly, setShowSalesOnly] = useState(false);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const handleShopSelect = (shop: Shop) => {
    setSelectedShop(shop);
    setIsPanelOpen(true);
  };

  const handleClosePanel = () => {
    setIsPanelOpen(false);
    setSelectedShop(null);
  };

  const toggleCategory = (category: ShopCategory) => {
    setActiveCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <Header />

      <FilterBar
        activeCategories={activeCategories}
        onToggleCategory={toggleCategory}
        showSalesOnly={showSalesOnly}
        onToggleSalesOnly={() => setShowSalesOnly(!showSalesOnly)}
      />

      <main className="flex-1 relative">
        <DustyMap
          selectedShop={selectedShop}
          onShopSelect={handleShopSelect}
          activeCategories={activeCategories}
          showSalesOnly={showSalesOnly}
        />

        <ShopPanel
          shop={selectedShop}
          isOpen={isPanelOpen}
          onClose={handleClosePanel}
        />
      </main>
    </div>
  );
}
