'use client'

import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useAuth } from './AuthProvider'

export default function AuthButton() {
    const { user } = useAuth()
    const [showPasswordPrompt, setShowPasswordPrompt] = useState(false)
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const router = useRouter()
    const supabase = createClient()

    const handleSignIn = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        const { error } = await supabase.auth.signInWithPassword({
            email: process.env.NEXT_PUBLIC_LOGIN_EMAIL || 'jantoeric@gmail.com',
            password: password,
        })

        if (error) {
            setError('Invalid password')
            setLoading(false)
        } else {
            setShowPasswordPrompt(false)
            setPassword('')
            router.refresh()
        }
    }

    const handleSignOut = async () => {
        await supabase.auth.signOut()
        router.refresh()
    }

    return (
        <div className="relative">
            {user ? (
                <button
                    onClick={handleSignOut}
                    className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
                    title={`Edit mode, logged in as ${user.email}`}
                >
                    Edit mode
                </button>
            ) : (
                <>
                    <button
                        onClick={() => setShowPasswordPrompt(!showPasswordPrompt)}
                        className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
                        title="Read mode"
                    >
                        Read mode
                    </button>

                    {showPasswordPrompt && (
                        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50">
                            <form onSubmit={handleSignIn}>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Password
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    placeholder="Enter password"
                                    autoFocus
                                />
                                {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
                                <div className="flex gap-2 mt-3">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowPasswordPrompt(false)
                                            setPassword('')
                                            setError('')
                                        }}
                                        className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={loading || !password}
                                        className="flex-1 px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                    >
                                        {loading ? 'Signing in...' : 'Sign In'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
