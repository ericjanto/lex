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
  if (isLoading) {
    return;
  }
  if (error) return <div>Error: {JSON.stringify(error)}</div>;

  const borderStyle = { border: "1px solid black", paddingRight: "5px" };

  return (
    <>
      <table style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th colSpan={2} style={borderStyle}>
              {data!.lemma}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={borderStyle}>Created</td>
            <td style={borderStyle}>
              {data!.created.substring(0, "yyyy-mm-dd".length)}
            </td>
          </tr>
          <tr>
            <td style={borderStyle}>Status</td>
            <td style={borderStyle}>
              <Status statusId={data!.status_id} />
            </td>
          </tr>
        </tbody>
      </table>
    </>
  );
}
