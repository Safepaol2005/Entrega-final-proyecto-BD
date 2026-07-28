"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CatalogView } from "@/components/CatalogView";

function CatalogInner() {
  const params = useSearchParams();
  const q = params.get("q") || "";
  return <CatalogView initialQ={q} />;
}

export default function CatalogPage() {
  return (
    <Suspense fallback={<div className="panel animate-pulse h-64" />}>
      <CatalogInner />
    </Suspense>
  );
}
