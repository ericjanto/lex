"use client";

import Link from "next/link";

export default function Page() {
  return (
    <ul style={{listStyleType: 'none', paddingLeft: '0', marginTop: '0'}}>
      <li>
        <Link href="/contexts">/contexts</Link>
      </li>
      <li>
        <Link href="/status/staged">/status/staged</Link>
      </li>
      <li>
        <Link href="/status/committed">/status/committed</Link>
      </li>
      <li>
        <Link href="/status/pushed">/status/pushed</Link>
      </li>
    </ul>
  );
}
