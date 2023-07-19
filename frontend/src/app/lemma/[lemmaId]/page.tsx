"use client";

import PaginatedContexts from "@/components/PaginatedContexts";
import Lemma from "@/components/Lemma";

export default function Page({ params }: { params: { lemmaId: number } }) {
  return (
    <>
      <Lemma lemmaId={params.lemmaId} />
      <br />
      <PaginatedContexts
        fetchQuery={`http://127.0.0.1:8000/lemma_contexts/${params.lemmaId}`}
        page_size={100}
      />
    </>
  );
}
