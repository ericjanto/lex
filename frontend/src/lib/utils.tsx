import Link, { LinkProps } from "next/link";

function appendId(
  clipboardText: string,
  id: number | string,
): string {
  const delimiter = '§'

  if (clipboardText.endsWith(delimiter)) {
    return clipboardText.slice(0, -delimiter.length) + " " + id + delimiter;
  }
  return id + " " + delimiter;
}

export function AppendCopyLink({
  children,
  toAppend,
  ...props
}: {
  children: any;
  toAppend: number | string;
} & LinkProps) {
  return (
    <Link
      {...props}
      onClick={(e) => {
        if (e.altKey && e.shiftKey) {
          // Read from clipboard and print to console
          navigator.clipboard.readText().then((text) => {
            const toCopy = appendId(text, toAppend);
            navigator.clipboard.writeText(toCopy);
          });
          e.preventDefault();
        }
      }}
    >
      {children}
    </Link>
  );
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
        
          <AppendCopyLink href={`/lemma/${id}`} toAppend={id}>
            {word}
          </AppendCopyLink>
          {space}
        </>
      );
    }
    return <>{value}</>;
  });
  return contextValueArrDeserialised;
}
