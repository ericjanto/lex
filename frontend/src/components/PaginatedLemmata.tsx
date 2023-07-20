import useSWRImmutable, { Fetcher } from "swr";

import { Lemma } from "@/components/Lemma";
import { useState } from "react";
import { AppendCopyLink } from "@/lib/utils";

export const fetcher: Fetcher<Lemma[]> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

function LemmaSetDisplayer({ fetchQuery }: { fetchQuery: string }) {
  const { data, error, isLoading } = useSWRImmutable(fetchQuery, fetcher);
  if (error) return <>{console.log(JSON.stringify(error))}</>;
  if (isLoading) return <></>;
  return (
    <>
      {data!.map((lemma: Lemma) => {
        return (
          <tr key={lemma.id}>
            <td>{lemma.id}</td>
            <td>
              <AppendCopyLink
                href={`/lemma/${lemma.id}`}
                toAppend={lemma.id}
              >
                {lemma.lemma}
              </AppendCopyLink>
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
  return (
    <>
      <table>
        <thead>
          <tr>
            <th style={{textAlign: 'left'}}>id</th>
            <th style={{textAlign: 'left'}}>lemma</th>
            <th style={{textAlign: 'left'}}>created</th>
          </tr>
        </thead>
        <tbody>
          {[...Array(page).keys()].map((i) => {
            return (
              <LemmaSetDisplayer
                key={i}
                fetchQuery={`${fetchQuery}&page=${
                  i + 1
                }&page_size=${page_size}`}
              />
            );
          })}
        </tbody>
      </table>
      <br />
      <button onClick={() => setPage(page + 1)}>Gimme more</button>
    </>
  );
}
