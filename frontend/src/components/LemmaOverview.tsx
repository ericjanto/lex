import useSWRImmutable, { Fetcher } from "swr";

import Status from "@/components/Status";
import { API_BASE_URL } from "@/lib/const";

export type Lemma = {
  id: number;
  lemma: string;
  created: string;
  status_id: number;
};

const lemmaFetcher: Fetcher<Lemma> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

export default function LemmaOverview({ lemmaId }: { lemmaId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `${API_BASE_URL}/lemma/${lemmaId}`,
    lemmaFetcher
  );
  if (isLoading) {
    return;
  }
  if (error) return <div>Error: {JSON.stringify(error)}</div>;

  const borderStyle = { border: "1px solid black", paddingRight: "5px" };

  if (data && Object.keys(data).length !== 0 && data.constructor === Object) {
    return (
      <>
        {data && (
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
                <td style={borderStyle}>created</td>
                <td style={borderStyle}>
                  {data!.created.substring(0, "yyyy-mm-dd".length)}
                </td>
              </tr>
              <tr>
                <td style={borderStyle}>status</td>
                <td style={borderStyle}>
                  <Status statusId={data!.status_id} />
                </td>
              </tr>
            </tbody>
          </table>
        )}
      </>
    );
  } else {
    return <div>Lemma with id {lemmaId} not found</div>;
  }
}
