import useSWRImmutable, { Fetcher } from "swr";

import { deserialiseContextValue } from "@/lib/utils";
import Paginator from "@/components/Paginator";

type Context = {
  id: number;
  context_value: string;
  created: string;
  source_id: number;
};

const fetcher: Fetcher<Context[]> = (url: RequestInfo | URL) =>
  fetch(url).then((r) => r.json());

function ContextSetDisplayer({ fetchQuery }: { fetchQuery: string }) {
  const { data, error, isLoading } = useSWRImmutable(fetchQuery, fetcher);

  if (error) return <div>Failed to load: ({JSON.stringify(error)})</div>;
  if (isLoading) return <div>Loading...</div>;
  return (
    <>
      {data!.map((context: Context) => {
        return (
          <span key={context.id}>
            <span style={{ color: "#919191" }}>{" § "}</span>
            <span>{deserialiseContextValue(context.context_value)}</span>
          </span>
        );
      })}
    </>
  );
}

export default function PaginatedContexts({
  fetchQuery,
  page_size,
}: {
  fetchQuery: string;
  page_size: number;
}) {
  return (
    <Paginator
      pageComponent={ContextSetDisplayer}
      fetchQuery={fetchQuery}
      page_size={page_size}
    />
  );
}
