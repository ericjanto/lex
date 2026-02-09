export const fetcher = (url: string) => {
    return fetch(url, {
        headers: {
            Authorization: `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
            apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
        },
    }).then((r) => r.json());
};
