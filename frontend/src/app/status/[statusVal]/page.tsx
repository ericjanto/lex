"use client";

import PaginatedLemmata from "@/components/PaginatedLemmata";

type StatusVal = "pending" | "accepted";

export default function Page({ params }: { params: { statusVal: StatusVal } }) {
  if (params.statusVal !== "pending" && params.statusVal !== "accepted") {
    return <div>Invalid status value</div>;
  }
  return (
    <PaginatedLemmata
      fetchQuery={`http://127.0.0.1:8000/status_lemmata?status_val=${params.statusVal}`}
      page_size={100}
    />
  );
}
