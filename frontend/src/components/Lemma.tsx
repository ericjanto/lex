import useSWRImmutable, { Fetcher } from "swr";

import Status from "@/components/Status";

export type Lemma = {
  id: number;
  lemma: string;
  created: string;
  status_id: number;
};

const lemmaFetcher: Fetcher<Lemma> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

export default function Lemma({ lemmaId }: { lemmaId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `http://127.0.0.1:8000/lemma/${lemmaId}`,
    lemmaFetcher
  );
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {JSON.stringify(error)}</div>;
  return (
    <div>
      <h1>{data!.lemma}</h1>
      <div>
        First encountered: {data!.created.substring(0, "yyyy-mm-dd".length)}
      </div>
      <Status statusId={data!.status_id} />
    </div>
  );
}
