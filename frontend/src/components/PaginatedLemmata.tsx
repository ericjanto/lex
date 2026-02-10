"use client";

import useSWRImmutable, { Fetcher } from "swr";

import { Lemma } from "@/components/LemmaOverview";
import Link from "next/link";
import { useEffect, useState } from "react";

function LemmaSetDisplayer({ fetchQuery }: { fetchQuery: string }) {
  const { data, error, isLoading } = useSWRImmutable(fetchQuery);

  if (error) {
    console.log(JSON.stringify(error));
    return <tr><td colSpan={3} style={{ color: 'red' }}>Error: {error.message || 'Failed to fetch'}</td></tr>;
  }
  if (isLoading) {
    return <tr><td colSpan={3}>Loading...</td></tr>;
  }

  if (!data || !Array.isArray(data)) {
    return (
      <tr>
        <td colSpan={3} style={{ color: 'orange' }}>
          {data?.error ? `API Error: ${data.error}` : 'No data or invalid format returned'}
        </td>
      </tr>
    );
  }

  return (
    <>
      {data.map((lemma: Lemma) => {
        return (
          <tr key={lemma.id}>
            <td>{lemma.id}</td>
            <td>
              <Link href={`/lemma/${lemma.id}`}>{lemma.lemma}</Link>
            </td>
            <td>{lemma.created}</td>
          </tr>
        );
      })}
    </>
  );
}

export default function PaginatedLemmata({
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

  return (
    <>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>id</th>
            <th style={{ textAlign: "left" }}>lemma</th>
            <th style={{ textAlign: "left" }}>created</th>
          </tr>
        </thead>
        <tbody id={"data-store"}>
          {[...Array(page).keys()].map((i) => {
            return (
              <LemmaSetDisplayer
                key={i}
                fetchQuery={`${fetchQuery}&page=${i + 1
                  }&page_size=${page_size}`}
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
