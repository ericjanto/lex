"use client";

import { SWRConfig } from "swr";
import { fetcher } from "@/lib/fetcher";

export const SWRProvider = ({ children }: { children: React.ReactNode }) => {
    return (
        <SWRConfig
            value={{
                fetcher: fetcher,
            }}
        >
            {children}
        </SWRConfig>
    );
};
