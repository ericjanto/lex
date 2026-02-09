"use client";

import useSWRImmutable, { Fetcher } from "swr";

import { API_BASE_URL } from "@/lib/const";
import Link from "next/link";

type SourceKind = {
  id: number;
  kind: string;
};

export default function SourceKind({ sourceKindId }: { sourceKindId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `${API_BASE_URL}/source_kind/${sourceKindId}`
  );
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {JSON.stringify(error)}</div>;
  return (
    <span>
      <Link href={`/sources?source_kind_id=${data!.id}`}>{data?.kind}</Link>
    </span>
  );
}
