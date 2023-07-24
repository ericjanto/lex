"use client";

import PaginatedContexts from "@/components/PaginatedContexts";
import SourceOverview from "@/components/SourceOverview";
import { API_BASE_URL } from "@/lib/const";

export default function Page({ params }: { params: { sourceId: number } }) {
  return (
    <>
      <SourceOverview sourceId={params.sourceId} />
      <br />
      <PaginatedContexts
        fetchQuery={`${API_BASE_URL}/source_contexts/${params.sourceId}`}
        page_size={100}
      />
    </>
  );
}
