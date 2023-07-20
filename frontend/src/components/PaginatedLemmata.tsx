import useSWRImmutable, { Fetcher } from "swr";

import { Lemma } from "@/components/Lemma";
import Paginator from "@/components/Paginator";
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
              <AppendCopyLink href={`/lemma/${lemma.id}`} toAppend={lemma.id}>
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
  return (
    <Paginator
      pageComponent={LemmaSetDisplayer}
      fetchQuery={fetchQuery}
      page_size={page_size}
    />
  );
}
