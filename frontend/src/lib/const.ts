const REMOTE_API_URL = 'https://ldmdsjurxfaefuehqezh.supabase.co/functions/v1/lex-api'
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || REMOTE_API_URL

export const getEnvHeaders = () => {
    if (process.env.NODE_ENV === 'development') {
        return { 'X-Environment': 'mock' }
    }
    return {}
}
