import useSWRImmutable, { Fetcher } from "swr";

import { API_BASE_URL } from "@/lib/const";
import SourceKind from "@/components/SourceKind";

export type Source = {
  id: number;
  title: string;
  source_kind_id: number;
};

const sourceFetcher: Fetcher<Source> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

export function SourceTitle({ sourceId }: { sourceId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `${API_BASE_URL}/source/${sourceId}`,
    sourceFetcher
  );

  if (error) {
    return <div>failed to load</div>;
  }
  if (isLoading) {
    return <div>loading...</div>;
  }

  return <>{data && data.title}</>;
}

export default function SourceOverview({ sourceId }: { sourceId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `${API_BASE_URL}/source/${sourceId}`,
    sourceFetcher
  );

  if (error) {
    return <div>failed to load</div>;
  }
  if (isLoading) {
    return <div>loading...</div>;
  }

  const borderStyle = { border: "1px solid black", paddingRight: "5px" };

  return (
    <>
      {data && (
        <table style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th colSpan={2} style={borderStyle}>
                {data!.title}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={borderStyle}>category</td>
              <td style={borderStyle}>
                <SourceKind sourceKindId={data!.source_kind_id} />
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </>
  );
}
