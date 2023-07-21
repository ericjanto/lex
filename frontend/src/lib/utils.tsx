import Link from "next/link";

export function appendQueryParams(
  href: string,
  params: { [key: string]: string | number } = {}
): string {
  const url = new URL(href);

  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value.toString());
  }
  return url.toString();
}

export function deserialiseContextValue(contextValue: string): JSX.Element[] {
  const contextValueObj = JSON.parse(contextValue);
  const contextValueArr = Object.values(contextValueObj) as string[];
  const contextValueArrDeserialised = contextValueArr.map((value: string) => {
    if (value.includes("::")) {
      let [word, id] = value.split("::");
      let space = "";
      if (id.endsWith(" ")) {
        id.trimEnd();
        space += " ";
      }
      return (
        <>
          <Link href={`/lemma/${id}`}>
            {word}
          </Link>
          {space}
        </>
      );
    }
    return <>{value}</>;
  });
  return contextValueArrDeserialised;
}
