"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { User, Session } from "@supabase/supabase-js";

type AuthContextType = {
    user: User | null;
    session: Session | null;
    loading: boolean;
};

const AuthContext = createContext<AuthContextType>({ user: null, session: null, loading: true });

export const useAuth = () => useContext(AuthContext);

export default function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);
    const supabase = createClient();

    useEffect(() => {
        const setData = async () => {
            const { data: { session }, error } = await supabase.auth.getSession();
            if (error) throw error;
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        };

        const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        setData();

        return () => {
            listener.subscription.unsubscribe();
        };
    }, [supabase]);

    const value = {
        session,
        user,
        loading
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
