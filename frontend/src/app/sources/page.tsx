"use client";

export const dynamic = "force-dynamic";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import PaginatedSources from "@/components/PaginatedSources";
import { API_BASE_URL } from "@/lib/const";

function SourcesContent() {
  const searchParams = useSearchParams();
  const searchParamsStr = searchParams.toString();

  return (
    <PaginatedSources
      fetchQuery={
        `${API_BASE_URL}/sources` +
        (searchParamsStr !== "" ? `?${searchParamsStr}` : "")
      }
      page_size={100}
    />
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SourcesContent />
    </Suspense>
  );
}
