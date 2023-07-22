import useSWRImmutable, { Fetcher } from "swr";

import { deserialiseContextValue } from "@/lib/utils";
import { useEffect, useState } from "react";

type Context = {
  id: number;
  context_value: string;
  created: string;
  source_id: number;
};

const fetcher: Fetcher<Context[]> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

function ContextSetDisplayer({ fetchQuery }: { fetchQuery: string }) {
  const { data, error, isLoading } = useSWRImmutable(fetchQuery, fetcher);

  if (error) return <div>Failed to load: ({JSON.stringify(error)})</div>;
  if (isLoading) return <div>Loading...</div>;
  return (
    <>
      {data!.map((context: Context) => {
        return (
          <span key={context.id} id={String(context.id)}>
            <span style={{ color: "#919191" }}>{" § "}</span>
            <span>{deserialiseContextValue(context.context_value)}</span>
          </span>
        );
      })}
    </>
  );
}

export default function PaginatedContexts({
  fetchQuery,
  page_size,
}: {
  fetchQuery: string;
  page_size: number;
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
