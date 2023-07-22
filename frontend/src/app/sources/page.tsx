"use client";

import { useSearchParams } from "next/navigation";

import PaginatedSources from "@/components/PaginatedSources";
import { API_BASE_URL } from "@/lib/const";

export default function Page() {
  const searchParams = useSearchParams();
  const source_kind_id = searchParams.get("source_kind_id");
  return (
    <PaginatedSources
      fetchQuery={
        `${API_BASE_URL}/sources` +
        (source_kind_id ? `?source_kind_id=${source_kind_id}` : "")
      }
      page_size={100}
    />
  );
}
