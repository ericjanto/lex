"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import useSWR from "swr";
import { API_BASE_URL } from "@/lib/const";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

type Lemma = {
    id: number;
    lemma: string;
};

const PAGE_SIZE = 50;

export default function ProcessLemmata({ sourceId }: { sourceId: number }) {
    const { session, loading: authLoading } = useAuth();
    const router = useRouter();
    const [ignoredLemmata, setIgnoredLemmata] = useState<Set<number>>(new Set());
    // translations: map of lemma id -> user-entered translation text
    const [translations, setTranslations] = useState<Record<number, string>>({});
    const [isSyncing, setIsSyncing] = useState(false);
    const [showLeaveDialog, setShowLeaveDialog] = useState(false);
    const [pendingNavigation, setPendingNavigation] = useState<string | null>(null);
    const [syncMessage, setSyncMessage] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [allLemmata, setAllLemmata] = useState<Lemma[]>([]);
    const [hasMore, setHasMore] = useState(true);
    const [lastCacheSave, setLastCacheSave] = useState<Date | null>(null);

    // Fetch page of new lemmata for this source
    const { data: fetchedPage, error, isLoading: dataLoading, mutate } = useSWR<Lemma[]>(
        `${API_BASE_URL}/status_lemmata?status_val=new&source_id=${sourceId}&page=${page}&page_size=${PAGE_SIZE}`
    );

    // Accumulate pages into allLemmata
    useEffect(() => {
        if (fetchedPage) {
            if (page === 1) {
                setAllLemmata(fetchedPage);
            } else {
                setAllLemmata(prev => {
                    const existingIds = new Set(prev.map(l => l.id));
                    const newItems = fetchedPage.filter(l => !existingIds.has(l.id));
                    return [...prev, ...newItems];
                });
            }
            if (fetchedPage.length < PAGE_SIZE) {
                setHasMore(false);
            }
        }
    }, [fetchedPage, page]);

    // Load state from local storage on mount
    useEffect(() => {
        const storedIgnored = localStorage.getItem(`ignoredLemmata_${sourceId}`);
        const storedTranslations = localStorage.getItem(`translations_${sourceId}`);
        const storedCacheTime = localStorage.getItem(`cacheTime_${sourceId}`);
        if (storedIgnored) {
            const parsed = JSON.parse(storedIgnored);
            if (parsed.length > 0) setIgnoredLemmata(new Set(parsed));
        }
        if (storedTranslations) {
            const parsed = JSON.parse(storedTranslations);
            if (Object.keys(parsed).length > 0) setTranslations(parsed);
        }
        if (storedCacheTime) {
            setLastCacheSave(new Date(storedCacheTime));
        }
    }, [sourceId]);

    // Save state to local storage on change
    useEffect(() => {
        const hasChanges = ignoredLemmata.size > 0 || Object.values(translations).some(v => v.trim() !== '');

        if (ignoredLemmata.size > 0) {
            localStorage.setItem(`ignoredLemmata_${sourceId}`, JSON.stringify(Array.from(ignoredLemmata)));
        } else {
            localStorage.removeItem(`ignoredLemmata_${sourceId}`);
        }

        const filledTranslations = Object.fromEntries(
            Object.entries(translations).filter(([, v]) => v.trim() !== '')
        );
        if (Object.keys(filledTranslations).length > 0) {
            localStorage.setItem(`translations_${sourceId}`, JSON.stringify(filledTranslations));
        } else {
            localStorage.removeItem(`translations_${sourceId}`);
        }

        if (hasChanges) {
            const now = new Date();
            localStorage.setItem(`cacheTime_${sourceId}`, now.toISOString());
            setLastCacheSave(now);
        }
    }, [ignoredLemmata, translations, sourceId]);

    // Count lemmata ready to sync (have non-empty translation)
    const toSyncCount = Object.values(translations).filter(v => v.trim() !== '').length;

    const hasUnsavedChanges = ignoredLemmata.size > 0 || toSyncCount > 0;

    // Intercept browser back/close with unsaved changes
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
            }
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [hasUnsavedChanges]);

    const handleNavigate = useCallback((path: string) => {
        if (hasUnsavedChanges) {
            setPendingNavigation(path);
            setShowLeaveDialog(true);
        } else {
            router.push(path);
        }
    }, [hasUnsavedChanges, router]);

    const handleDiscardCache = () => {
        localStorage.removeItem(`ignoredLemmata_${sourceId}`);
        localStorage.removeItem(`translations_${sourceId}`);
        localStorage.removeItem(`cacheTime_${sourceId}`);
        setIgnoredLemmata(new Set());
        setTranslations({});
        setLastCacheSave(null);
        setShowLeaveDialog(false);
        if (pendingNavigation) {
            router.push(pendingNavigation);
        }
    };

    const handleContinueLater = () => {
        setShowLeaveDialog(false);
        if (pendingNavigation) {
            router.push(pendingNavigation);
        }
    };

    const handleDiscard = (id: number) => {
        const newIgnored = new Set(ignoredLemmata);
        newIgnored.add(id);
        setIgnoredLemmata(newIgnored);

        // Remove translation if present
        if (translations[id]) {
            const newTranslations = { ...translations };
            delete newTranslations[id];
            setTranslations(newTranslations);
        }
    };

    const handleUndoDiscard = (id: number) => {
        const newIgnored = new Set(ignoredLemmata);
        newIgnored.delete(id);
        setIgnoredLemmata(newIgnored);
    };

    const handleTranslationChange = (id: number, value: string) => {
        setTranslations(prev => ({ ...prev, [id]: value }));
    };

    const handleSync = async () => {
        setIsSyncing(true);
        setSyncMessage("Syncing...");
        try {
            // 1. Insert ignored lemmata to lemma_ignored table
            if (ignoredLemmata.size > 0) {
                const ignoredPayload = Array.from(ignoredLemmata).map(id => {
                    const l = allLemmata?.find(item => item.id === id);
                    return { lemma: l?.lemma, source_id: Number(sourceId) };
                }).filter(i => i.lemma);

                await fetch(`${API_BASE_URL}/bulk_lemma_ignored`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${session?.access_token}`,
                        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
                    },
                    body: JSON.stringify(ignoredPayload)
                });

                // Delete ignored lemmata from lemma table
                try {
                    const deleteRes = await fetch(`${API_BASE_URL}/lemma`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${session?.access_token}`,
                            apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
                        },
                        body: JSON.stringify(Array.from(ignoredLemmata))
                    });
                    if (!deleteRes.ok) {
                        const errTxt = await deleteRes.text();
                        console.error('Lemma deletion failed:', errTxt);
                        throw new Error(`Deletion failed: ${errTxt}`);
                    }
                } catch (delErr: any) {
                    console.error('Network or server error during deletion:', delErr);
                    throw new Error(`Lemma deletion failed. Please check your connection or server logs. ${delErr.message}`);
                }
            }

            // 2. Submit Anki cards — use translation as Back instead of context
            const ankiIds = Object.entries(translations)
                .filter(([, v]) => v.trim() !== '')
                .map(([id]) => Number(id));

            for (const id of ankiIds) {
                const l = allLemmata?.find(item => item.id === id);
                if (!l) continue;

                const translation = translations[id].trim();

                const ankiUrl = API_BASE_URL.replace(/\/lex-api$/, '/anki-connect');
                const response = await fetch(ankiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${session?.access_token}`,
                        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
                    },
                    body: JSON.stringify({
                        action: 'addNote',
                        params: {
                            lemma: l.lemma,
                            translation: translation,
                            source: '',
                            source_url: '',
                            lemma_id: l.id
                        }
                    })
                });
                if (!response.ok) {
                    const errorText = await response.text();
                    if (errorText.includes('duplicate')) {
                        console.warn(`Skipping duplicate Anki note for: ${l.lemma}`);
                        continue;
                    }
                    console.error('Anki sync failed for', l.lemma, errorText);
                    throw new Error(`Failed to sync ${l.lemma}: ${errorText}`);
                }
            }

            // 3. Update status to 'learning' for synced lemmata
            if (ankiIds.length > 0) {
                const statusRes = await fetch(`${API_BASE_URL}/status`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${session?.access_token}`,
                        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
                    },
                    body: JSON.stringify({
                        lemma_ids: ankiIds,
                        new_status_id: 2
                    })
                });
                if (!statusRes.ok) {
                    const errText = await statusRes.text();
                    console.error('Status update failed:', errText);
                    throw new Error(`Status update failed: ${errText}`);
                }
            }

            // 4. Trigger Anki headless client sync (AnkiWeb upload)
            if (ankiIds.length > 0) {
                try {
                    const ankiUrl = API_BASE_URL.replace(/\/lex-api$/, '/anki-connect');
                    await fetch(ankiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${session?.access_token}`,
                            apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
                        },
                        body: JSON.stringify({ action: 'sync' })
                    });
                } catch (syncErr) {
                    console.warn('AnkiWeb sync trigger failed (cards were still added):', syncErr);
                }
            }

            // Clear local state
            setIgnoredLemmata(new Set());
            setTranslations({});
            localStorage.removeItem(`ignoredLemmata_${sourceId}`);
            localStorage.removeItem(`translations_${sourceId}`);
            localStorage.removeItem(`cacheTime_${sourceId}`);
            setLastCacheSave(null);

            // Reset pagination and re-fetch
            setPage(1);
            setAllLemmata([]);
            setHasMore(true);
            await mutate();
            const syncedNames = ankiIds.map(id => allLemmata?.find(item => item.id === id)?.lemma).filter(Boolean);
            const discardedNames = Array.from(ignoredLemmata).map(id => allLemmata?.find(item => item.id === id)?.lemma).filter(Boolean);

            setSyncMessage(`Sync complete!
                Added: ${syncedNames.join(', ') || 'none'}
                Discarded: ${discardedNames.join(', ') || 'none'}`);
            setTimeout(() => setSyncMessage(null), 10000); // 10s so it's readable

        } catch (e: any) {
            console.error(e);
            setSyncMessage(`Sync failed: ${e.message}`);
        } finally {
            setIsSyncing(false);
        }
    };

    if (error) return <div className="text-red-500">Error loading lemmata: {error.message}</div>;

    const visibleLemmata = allLemmata.filter(l => !ignoredLemmata.has(l.id));

    // Format cache time
    const cacheAgo = lastCacheSave
        ? (() => {
            const diff = Math.floor((Date.now() - lastCacheSave.getTime()) / 1000);
            if (diff < 60) return `${diff}s ago`;
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            return `${Math.floor(diff / 3600)}h ago`;
        })()
        : null;

    return (
        <div className="p-4 max-w-4xl mx-auto">
            {/* Leave page dialog */}
            {showLeaveDialog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
                        <h2 className="text-lg font-bold mb-2">Unsaved Changes</h2>
                        <p className="text-gray-600 mb-4">
                            You have {ignoredLemmata.size} discarded and {toSyncCount} to-sync lemmata cached locally.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={handleContinueLater}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                                Continue Later
                            </button>
                            <button
                                onClick={handleDiscardCache}
                                className="flex-1 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
                            >
                                Discard Cache
                            </button>
                            <button
                                onClick={() => setShowLeaveDialog(false)}
                                className="px-4 py-2 bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {(authLoading || (dataLoading && allLemmata.length === 0)) && (
                <div className="p-4 bg-yellow-50 text-yellow-800 rounded mb-4 animate-pulse">
                    {authLoading ? "Checking authentication..." : "Fetching lemmata data..."}
                </div>
            )}

            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold">Process New Lemmata</h1>
                    {syncMessage && (
                        <div className={`mt-2 p-2 rounded text-sm ${syncMessage.includes('failed') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                            {syncMessage}
                        </div>
                    )}
                    {!session && !authLoading && (
                        <div className="mt-2 text-sm text-amber-600 font-medium italic">
                            ⚠️ Sign in to Discard or Sync with Anki
                        </div>
                    )}
                </div>
                <div className="flex gap-4 items-center">
                    {cacheAgo && (
                        <div className="text-xs text-gray-400" title="Last saved to local cache">
                            💾 {cacheAgo}
                        </div>
                    )}
                    <div className="text-sm text-gray-500">
                        {ignoredLemmata.size} discarded, {toSyncCount} to sync
                    </div>
                    <button
                        onClick={handleSync}
                        disabled={isSyncing || (ignoredLemmata.size === 0 && toSyncCount === 0) || !session}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSyncing ? "Syncing..." : "Sync with Anki"}
                    </button>
                    <button
                        onClick={() => handleNavigate('/learn')}
                        className="text-gray-500 hover:text-gray-700"
                    >
                        Back
                    </button>
                </div>
            </div>

            {/* Table of lemmata */}
            <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="bg-gray-50 border-b">
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600 w-1/3">Lemma</th>
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Translation (Anki Back)</th>
                            <th className="px-4 py-3 w-12"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {visibleLemmata.map(l => {
                            const translation = translations[l.id] || '';
                            const isReady = translation.trim() !== '';
                            return (
                                <tr
                                    key={l.id}
                                    className="border-b last:border-b-0 transition-colors bg-white hover:bg-gray-50"
                                >
                                    <td className="px-4 py-3">
                                        <span className="text-lg font-medium text-gray-900">
                                            {l.lemma}
                                        </span>
                                    </td>
                                    <td className="px-4 py-2">
                                        <input
                                            type="text"
                                            value={translation}
                                            onChange={(e) => handleTranslationChange(l.id, e.target.value)}
                                            disabled={!session}
                                            placeholder="Enter translation..."
                                            className="w-full px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-30 border-gray-200 bg-white"
                                        />
                                    </td>
                                    <td className="px-2 py-3 text-center">
                                        <button
                                            onClick={() => handleDiscard(l.id)}
                                            disabled={!session}
                                            className="text-red-400 hover:text-red-600 p-1.5 rounded-full hover:bg-red-50 transition-colors disabled:opacity-30"
                                            title="Discard (Ignore)"
                                        >
                                            ✕
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Load more */}
            {
                hasMore && allLemmata.length > 0 && (
                    <div className="mt-4 text-center">
                        <button
                            onClick={() => setPage(p => p + 1)}
                            disabled={dataLoading}
                            className="px-6 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                        >
                            {dataLoading ? "Loading..." : "Load more"}
                        </button>
                    </div>
                )
            }
            {
                !hasMore && allLemmata.length > 0 && (
                    <div className="mt-4 text-center text-sm text-gray-400">
                        All {allLemmata.length} lemmata loaded
                    </div>
                )
            }

            {
                allLemmata.length > 0 && visibleLemmata.length === 0 && (
                    <div className="text-center py-10 text-gray-500 bg-gray-50 rounded-lg border border-dashed mt-4">
                        All lemmata have been processed!
                        <div className="mt-4">
                            <button
                                onClick={() => handleNavigate('/learn')}
                                className="text-blue-600 hover:underline"
                            >
                                Go back to overview
                            </button>
                        </div>
                    </div>
                )
            }

            {
                allLemmata.length === 0 && !dataLoading && (
                    <div className="text-center py-10 text-gray-500 bg-gray-50 rounded-lg border border-dashed">
                        No new lemmata to process!
                        <div className="mt-4">
                            <button
                                onClick={() => handleNavigate('/learn')}
                                className="text-blue-600 hover:underline"
                            >
                                Go back to overview
                            </button>
                        </div>
                    </div>
                )
            }

            {/* Undo Section */}
            {
                ignoredLemmata.size > 0 && (
                    <div className="mt-8 border-t pt-4">
                        <h3 className="text-lg font-semibold mb-2 text-gray-700">Discarded (Undo?)</h3>
                        <div className="flex flex-wrap gap-2">
                            {Array.from(ignoredLemmata).map(id => {
                                const l = allLemmata?.find(i => i.id === id);
                                return (
                                    <button
                                        key={id}
                                        onClick={() => handleUndoDiscard(id)}
                                        className="px-3 py-1 bg-gray-100 rounded-full text-sm hover:bg-gray-200 flex items-center gap-1 border border-gray-300"
                                    >
                                        {l?.lemma ?? `ID ${id}`} <span className="text-gray-400 ml-1">↩</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                )
            }
        </div >
    );
}
