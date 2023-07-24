import useSWRImmutable, { Fetcher } from "swr";

import { API_BASE_URL } from "@/lib/const";
import SourceKind from "@/components/SourceKind";
import Link from "next/link";

export type Source = {
  id: number;
  title: string;
  source_kind_id: number;
  author: string;
  lang: string;
  removed_lemmata_num: number;
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
              <td style={borderStyle}>author</td>
              <td style={borderStyle}>
                <Link href={`/sources?author=${data!.author}`}>
                  {data!.author}
                </Link>
              </td>
            </tr>
            <tr>
              <td style={borderStyle}>category</td>
              <td style={borderStyle}>
                <SourceKind sourceKindId={data!.source_kind_id} />
              </td>
            </tr>
            <tr>
              <td style={borderStyle}>language</td>
              <td style={borderStyle}>
                <Link href={`/sources?lang=${data!.lang}`}>{data?.lang}</Link>
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </>
  );
}
