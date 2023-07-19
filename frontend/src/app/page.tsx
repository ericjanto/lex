"use client";

import PaginatedContexts from "@/components/PaginatedContexts";

export default function Page() {
  return (
    <PaginatedContexts
      fetchQuery={"http://127.0.0.1:8000/contexts"}
      page_size={100}
    />
  );
}
