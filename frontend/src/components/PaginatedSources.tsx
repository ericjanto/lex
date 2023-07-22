import useSWRImmutable, { Fetcher } from "swr";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Source } from "@/components/SourceOverview";
import SourceKind from "@/components/SourceKind";

const fetcher: Fetcher<Source[]> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

function SourceSetDisplayer({ fetchQuery }: { fetchQuery: string }) {
  const { data, error, isLoading } = useSWRImmutable(fetchQuery, fetcher);
  if (error) {
    console.log(JSON.stringify(error));
    return;
  }
  if (isLoading) {
    return;
  }

  if (!data) {
    return;
  }

  return (
    <>
      {data!.map((source: Source) => {
        return (
          <tr key={source.id}>
            <td>{source.id}</td>
            <td>
              <Link href={`/source/${source.id}`}>{source.title}</Link>
            </td>
            <td>
              <SourceKind sourceKindId={source.source_kind_id} />
            </td>
          </tr>
        );
      })}
    </>
  );
}

export default function PaginatedSources({
  fetchQuery,
  page_size,
}: {
  fetchQuery: string;
  page_size: number;
}) {
  const [page, setPage] = useState(1);
  const [allLoaded, setAllLoaded] = useState(false);

  useEffect(() => {
    const dataStore = document.getElementById("data-store");
    const trs = dataStore ? dataStore.getElementsByTagName("tr") : [];
    if (trs.length < (page - 1) * page_size) {
      setAllLoaded(true);
    } else {
      setAllLoaded(false);
    }
  }, [page, page_size]);

  console.log(fetchQuery);
  return (
    <>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>id</th>
            <th style={{ textAlign: "left" }}>title</th>
            <th style={{ textAlign: "left" }}>category</th>
          </tr>
        </thead>
        <tbody id={"data-store"}>
          {[...Array(page).keys()].map((i) => {
            return (
              <SourceSetDisplayer
                key={i}
                fetchQuery={
                  fetchQuery.includes("?")
                    ? `${fetchQuery}&page=${i + 1}&page_size=${page_size}`
                    : `${fetchQuery}?page=${i + 1}&page_size=${page_size}`
                }
              />
            );
          })}
        </tbody>
      </table>
      <br />
      {!allLoaded && (
        <button onClick={() => setPage(page + 1)}>Load more</button>
      )}
      {allLoaded && <div>All data returned. ₍ᐢ. ̫.ᐢ₎</div>}
    </>
  );
}
