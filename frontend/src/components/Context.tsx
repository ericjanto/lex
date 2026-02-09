"use client";

import Link from "next/link";
import { useState } from "react";

export type Context = {
  id: number;
  context_value: string;
  created: string;
  source_id: number;
};

export function Context({
  context,
  highlightedLemmaId,
}: {
  context: Context;
  highlightedLemmaId?: number;
}) {
  const [hovered, setHovered] = useState(false);

  let contextValueObj;
  try {
    contextValueObj = JSON.parse(context.context_value);
  } catch (e) {
    // Fallback for non-JSON content
    contextValueObj = { "0": context.context_value };
  }

  const contextValueArr = Object.values(contextValueObj) as string[];
  const contextValueArrDeserialised = contextValueArr.map((value: string, index: number) => {
    if (value.includes("::")) {
      let [word, id] = value.split("::");
      let space = "";
      if (id.endsWith(" ")) {
        id = id.trimEnd();
        space += " ";
      }
      return (
        <span key={index}>
          <Link
            href={`/lemma/${id}`}
            style={
              parseInt(id) == highlightedLemmaId
                ? { backgroundColor: "yellow" }
                : {}
            }
          >
            {word}
          </Link>
          {space}
        </span>
      );
    }
    return <span key={index}>{value}</span>;
  });

  return (
    <span
      id={String(context.id)}
      onMouseOver={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {" "}
      <Link
        href={`/context/${context.id}`}
        style={{
          textDecoration: "None",
        }}
      >
        <span style={{ border: hovered ? "1.5px solid black" : "" }}>{"§"}</span>
      </Link>
      {" "}
      <span style={{ backgroundColor: hovered ? "rgb(229 238 254)" : "" }}>
        {contextValueArrDeserialised}
      </span>
    </span>
  );
}
