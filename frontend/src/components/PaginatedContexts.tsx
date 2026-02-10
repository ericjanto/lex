"use client";

import useSWRImmutable, { Fetcher } from "swr";

import { Context } from "@/components/Context";
import { useEffect, useState } from "react";

function ContextSetDisplayer({
  fetchQuery,
  highlightedLemmaId,
}: {
  fetchQuery: string;
  highlightedLemmaId?: number;
}) {
  const { data, error, isLoading } = useSWRImmutable(fetchQuery);

  if (!Array.isArray(data)) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg">
        <p className="font-bold">Invalid response format</p>
        <p className="text-sm">Expected an array of contexts, but received:</p>
        <pre className="mt-2 text-xs overflow-auto max-h-40 bg-red-100 p-2 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <>
      {data.map((context: Context) => {
        return (
          <span key={context.id} id={String(context.id)}>
            <Context
              key={context.id}
              context={context}
              highlightedLemmaId={highlightedLemmaId}
            />
          </span>
        );
      })}
    </>
  );
}

export default function PaginatedContexts({
  fetchQuery,
  page_size,
  highlightedLemmaId,
}: {
  fetchQuery: string;
  page_size: number;
  highlightedLemmaId?: number;
}) {
  const [page, setPage] = useState(1);
  const [allLoaded, setAllLoaded] = useState(false);

  useEffect(() => {
    const spans = document.getElementsByTagName("span");
    const contextSpans = Array.from(spans).filter((span) => {
      return span.innerText.includes(" § ");
    });

    if (contextSpans.length < (page - 1) * page_size) {
      setAllLoaded(true);
    } else {
      setAllLoaded(false);
    }
  }, [page, page_size]);

  return (
    <>
      {[...Array(page).keys()].map((i) => {
        return (
          <ContextSetDisplayer
            key={i}
            fetchQuery={`${fetchQuery}?page=${i + 1}&page_size=${page_size}`}
            highlightedLemmaId={highlightedLemmaId}
          />
        );
      })}
      <br />
      {!allLoaded && (
        <button onClick={() => setPage(page + 1)}>Load more</button>
      )}
      {allLoaded && <div>All data returned. ₍ᐢ. ̫.ᐢ₎</div>}
    </>
  );
}
