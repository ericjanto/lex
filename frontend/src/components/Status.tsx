import useSWRImmutable, { Fetcher } from "swr";

import { StatusVal } from "@/app/status/[statusVal]/page";

type Status = {
  id: number;
  status: StatusVal;
};

function functionalColour(status: StatusVal) {
  switch (status) {
    case "staged":
      return "red";
    case "committed":
      return "yellow";
    case "pushed":
      return "green";
  }
}

const fetcher: Fetcher<Status> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

export default function Status({ statusId }: { statusId: number }) {
  const { data, error, isLoading } = useSWRImmutable(
    `http://127.0.0.1:8000/lemma_status_by_id/${statusId}`,
    fetcher
  );
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {JSON.stringify(error)}</div>;
  return (
    <span style={{ color: functionalColour(data!.status) }}>
      {data!.status}
    </span>
  );
}
