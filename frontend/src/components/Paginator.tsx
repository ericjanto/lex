import { useState, FC } from "react";

export default function Paginator({
  pageComponent: PageComponent,
  fetchQuery,
  page_size,
}: {
  pageComponent: FC<{ fetchQuery: string }>;
  fetchQuery: string;
  page_size: number;
}) {
  const [page, setPage] = useState(1);
  return (
    <>
      {[...Array(page).keys()].map((i) => {
        return (
          <PageComponent
            key={i}
            fetchQuery={`${fetchQuery}?page=${i + 1}&page_size=${page_size}`}
          />
        );
      })}
      <br />
      <button onClick={() => setPage(page + 1)}>Load more</button>
    </>
  );
}
