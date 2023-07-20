"use client";

import PaginatedLemmata from "@/components/PaginatedLemmata";
import { API_BASE_URL } from "@/lib/const";

export type StatusVal = "staged" | "committed" | "pushed";

export default function Page({ params }: { params: { statusVal: StatusVal } }) {
  if (
    params.statusVal !== "staged" &&
    params.statusVal !== "committed" &&
    params.statusVal !== "pushed"
  ) {
    return <div>Invalid status value</div>;
  }
  return (
    <PaginatedLemmata
      fetchQuery={`${API_BASE_URL}/status_lemmata?status_val=${params.statusVal}`}
      page_size={100}
    />
  );
}
