"use client";

import PaginatedContexts from "@/components/PaginatedContexts";
import { API_BASE_URL } from "@/lib/const";

export default function Page() {
  return (
    <PaginatedContexts
      fetchQuery={`${API_BASE_URL}/contexts`}
      page_size={100}
    />
  );
}
