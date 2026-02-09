"use client";

import useSWRImmutable, { Fetcher } from "swr";

import { StatusVal } from "@/app/status/[statusVal]/page";
import { API_BASE_URL } from "@/lib/const";
import Link from "next/link";

type Status = {
  id: number;
  status: StatusVal;
};

function functionalColour(status: StatusVal) {
  switch (status) {
    case "new":
      return "red";
    case "synced":
      return "orange";
    case "learned":
      return "green";
  }
}

export default function Status({ statusId }: { statusId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `${API_BASE_URL}/lemma_status_by_id/${statusId}`
  );
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {JSON.stringify(error)}</div>;
  return (
    <span>
      <Link
        href={`/status/${data!.status}`}
        style={{ color: functionalColour(data!.status) }}
      >
        {data!.status}
      </Link>
    </span>
  );
}
