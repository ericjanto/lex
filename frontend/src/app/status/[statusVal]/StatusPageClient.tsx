"use client";

import PaginatedLemmata from "@/components/PaginatedLemmata";
import { API_BASE_URL } from "@/lib/const";
import { useEffect, useState } from "react";
import { StatusVal } from "./page";

export default function StatusPageClient({ statusVal }: { statusVal: StatusVal }) {
    const [copiedIds, setCopiedIds] = useState<number[]>([]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.key === "c") {
                const { activeElement } = document;
                if (activeElement instanceof HTMLAnchorElement) {
                    const { href } = activeElement;
                    const idStr = href.split("/").pop();
                    const id = idStr ? parseInt(idStr) : NaN;
                    setCopiedIds((prev) => {
                        if (prev.includes(id) || isNaN(id)) {
                            return prev;
                        }
                        return [...prev, id];
                    });
                }
            }

            if (e.shiftKey && e.ctrlKey && e.key === "C") {
                navigator.clipboard.writeText(copiedIds.join(" "));
                setCopiedIds([]);
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [copiedIds]);

    const grid = (
        <div
            style={{
                display: "grid",
                gridTemplateColumns: "repeat(5, 1fr)",
                gridTemplateRows: `repeat(${Math.ceil(copiedIds.length / 5)}, 1fr)`,
                gap: "2px",
            }}
        >
            {copiedIds
                .sort((a, b) => a - b)
                .map((id) => (
                    <code
                        key={id}
                        style={{
                            border: "1px solid black",
                            padding: "2px",
                            textAlign: "center",
                        }}
                    >
                        {id}
                    </code>
                ))}
        </div>
    );

    return (
        <>
            <details
                style={{
                    position: "fixed",
                    top: "8px",
                    right: "8px",
                    fontSize: "12px",
                    border: "1px solid black",
                    padding: "2px",
                }}
            >
                <summary>CLI Helpers</summary>
                <div>
                    <code>tab</code> to focus
                </div>
                <div>
                    <code>ctrl+c</code> to store
                </div>
                <div>
                    <code>shift+ctrl+c</code> to copy
                </div>
                {copiedIds.length > 0 && <br />}
                <div>{grid}</div>
            </details>
            <PaginatedLemmata
                fetchQuery={`${API_BASE_URL}/status_lemmata?status_val=${statusVal}`}
                page_size={100}
            />
        </>
    );
}
