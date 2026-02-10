"use client";

import useSWR from "swr";
import { API_BASE_URL } from "@/lib/const";
import Link from "next/link";
import { useState } from "react";
import { useAuth } from "./AuthProvider";

type SourceOverview = {
    id: number;
    title: string;
    author: string;
    word_count: number | null;
    new_count: number;
    learning_count: number;
    learned_count: number;
    max_learned_position: number;
};

export default function LearnOverview() {
    const { session } = useAuth();
    const { data, error, isLoading, mutate } = useSWR<SourceOverview[]>(
        `${API_BASE_URL}/learn/overview`
    );
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState<{ updated_count: number } | null>(null);

    const handleSyncMaturity = async () => {
        if (!session?.access_token) return;
        setIsSyncing(true);
        try {
            const res = await fetch(`${API_BASE_URL}/sync_anki_maturity`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${session.access_token}`,
                    apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
                }
            });
            if (res.ok) {
                const data = await res.json();
                setSyncResult(data);
                mutate();
                setTimeout(() => setSyncResult(null), 5000);
            }
        } catch (err) {
            console.error('Maturity sync failed:', err);
        } finally {
            setIsSyncing(false);
        }
    };

    if (isLoading) return <div>Loading...</div>;
    if (error) return <div>Error loading learn overview</div>;

    return (
        <div className="p-4 max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Learning Process</h1>
                <div className="flex items-center gap-2">
                    {syncResult && (
                        <span className="text-sm text-green-600 font-medium animate-fade-in">
                            Updated {syncResult.updated_count} cards
                        </span>
                    )}
                    <button
                        onClick={handleSyncMaturity}
                        disabled={isSyncing}
                        className={`px-4 py-2 rounded text-sm font-medium transition-all ${isSyncing
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white border hover:bg-gray-50 text-gray-700 shadow-sm'
                            }`}
                    >
                        {isSyncing ? 'Syncing...' : 'Sync Maturity'}
                    </button>
                </div>
            </div>
            <div className="space-y-6">
                {Array.isArray(data) && data.map((source) => {
                    const totalLemmata = source.new_count + source.learning_count + source.learned_count;
                    const coveragePercent = source.word_count
                        ? ((source.max_learned_position / source.word_count) * 100).toFixed(1)
                        : "N/A";

                    return (
                        <div key={source.id} className="border p-4 rounded-lg shadow-sm bg-white">
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <h2 className="text-lg font-semibold">{source.title}</h2>
                                    <p className="text-gray-600 text-sm">{source.author}</p>
                                </div>
                                <div className="text-right">
                                    <div className="text-2xl font-bold">{coveragePercent}%</div>
                                    <div className="text-xs text-gray-500">Coverage</div>
                                </div>
                            </div>

                            <div className="mb-2">
                                <div className="flex h-4 rounded-full overflow-hidden bg-gray-100">
                                    {totalLemmata > 0 ? (
                                        <>
                                            <div
                                                style={{ width: `${(source.learned_count / totalLemmata) * 100}%` }}
                                                className="bg-green-500"
                                                title={`Learned: ${source.learned_count}`}
                                            />
                                            <div
                                                style={{ width: `${(source.learning_count / totalLemmata) * 100}%` }}
                                                className="bg-orange-400"
                                                title={`Learning: ${source.learning_count}`}
                                            />
                                            <div
                                                style={{ width: `${(source.new_count / totalLemmata) * 100}%` }}
                                                className="bg-red-500"
                                                title={`New: ${source.new_count}`}
                                            />
                                        </>
                                    ) : (
                                        <div className="w-full h-full bg-gray-200" />
                                    )}
                                </div>
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>{source.learned_count} learned</span>
                                    <span>{source.learning_count} learning</span>
                                    <span>{source.new_count} new</span>
                                </div>
                            </div>

                            <div className="flex justify-end mt-4">
                                <Link
                                    href={`/learn/${source.id}/process`}
                                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium transition-colors"
                                >
                                    Process Lemmata
                                </Link>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
