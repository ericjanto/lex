"use client";

import { useSearchParams } from "next/navigation";

import PaginatedSources from "@/components/PaginatedSources";
import { API_BASE_URL } from "@/lib/const";

export default function Page() {
  const searchParamsStr = useSearchParams().toString();

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
