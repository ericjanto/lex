import Link from "next/link";

// fetch data
async function getData() {
  const res = await fetch(
    "http://127.0.0.1:8000/contexts?page=1&page_size=500"
  );
  // The return value is *not* serialized
  // You can return Date, Map, Set, etc.

  // Recommendation: handle errors
  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error("Failed to fetch data");
  }

  return res.json();
}

// deserialise context_value
// first, parse the JSON string into an object
// then, iterate through the object and convert the values
// each value is a string, e.g. 'word' or 'word::id'.
// if the value is simply a word, without an id (e.g. 'word' instead of 'word::id'),
// then just return the word.
// otherwise create a link. See the following example:
// input: '["word1 ", "word2::id "]'
// output: <span>word1 </span><Link to="/lemma/id">word2 </Link>
// note that the trailing space is preserved
function deserialiseContextValue(contextValue: string): JSX.Element[] {
  const contextValueObj = JSON.parse(contextValue);
  const contextValueArr = Object.values(contextValueObj);
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
          <Link href={`/lemma/${id}`}>{word}</Link>
          {space}
        </>
      );
    }
    return `${value}`;
  });
  return contextValueArrDeserialised;
}

export default async function Page() {
  const data = await getData();
  return (
    <div>
      {data.map((item: any) => {
        return (
          <span>
            <span style={{ color: "#919191" }}>{" § "}</span>
            {deserialiseContextValue(item.context_value)}
          </span>
        );
      })}
    </div>
  );
}
