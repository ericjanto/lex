"use client";

import PaginatedLemmata from "@/components/PaginatedLemmata";

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
      fetchQuery={`http://127.0.0.1:8000/status_lemmata?status_val=${params.statusVal}`}
      page_size={100}
    />
  );
}
