"use client";

import PaginatedContexts from "@/components/PaginatedContexts";
import Lemma from "@/components/Lemma";
import { API_BASE_URL } from "@/lib/const";

export default function Page({ params }: { params: { lemmaId: number } }) {
  return (
    <>
      <Lemma lemmaId={params.lemmaId} />
      <br />
      <PaginatedContexts
        fetchQuery={`${API_BASE_URL}/lemma_contexts/${params.lemmaId}`}
        page_size={100}
      />
    </>
  );
}
