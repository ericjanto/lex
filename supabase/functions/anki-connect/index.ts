import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
}

serve(async (req) => {
    // Handle CORS
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const authHeader = req.headers.get('Authorization')
        if (!authHeader) {
            throw new Error('Missing Authorization header')
        }

        const supabaseClient = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_ANON_KEY') ?? '',
            {
                global: { headers: { Authorization: authHeader } },
            }
        )

        // Verify the user is authenticated
        const { data: { user }, error: authError } = await supabaseClient.auth.getUser()
        if (authError || !user) {
            return new Response(JSON.stringify({ error: 'Unauthorized' }), {
                status: 401,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        const { action, params } = await req.json()
        const ankiConnectUrl = Deno.env.get('ANKI_CONNECT_URL')

        if (!ankiConnectUrl) {
            throw new Error('ANKI_CONNECT_URL is not configured')
        }

        // Logic for specific actions
        if (action === 'addNote') {
            const { lemma, context, source, source_url } = params

            // Construct the AnkiConnect payload
            // Assuming a specific Note Type and Deck. These could be configurable or passed in params.
            // For now, let's use sensible defaults or env vars if available.
            const deckName = Deno.env.get('ANKI_DECK_NAME') || 'Lex'
            const modelName = Deno.env.get('ANKI_MODEL_NAME') || 'Basic'

            const payload = {
                action: 'addNote',
                version: 6,
                params: {
                    note: {
                        deckName: deckName,
                        modelName: modelName,
                        fields: {
                            Front: lemma, // Or whatever fields the user's model has
                            Back: `${context} <br><br> <small>${source}</small>`,
                            // Add more fields if necessary
                        },
                        options: {
                            allowDuplicate: false,
                            duplicateScope: 'deck',
                            duplicateScopeOptions: {
                                deckName: deckName,
                                checkChildren: false,
                                checkAllModels: false
                            }
                        },
                        tags: ['lex_generated']
                    }
                }
            }

            // Forward to AnkiConnect
            const ankiResponse = await fetch(ankiConnectUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            const ankiResult = await ankiResponse.json()

            if (ankiResult.error) {
                throw new Error(`AnkiConnect Error: ${ankiResult.error}`)
            }

            return new Response(JSON.stringify({ success: true, noteId: ankiResult.result }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // Generic proxy for other actions if needed (e.g. getDecks, sync)
        if (action === 'sync') {
            const payload = {
                action: 'sync',
                version: 6
            }
            const ankiResponse = await fetch(ankiConnectUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            const ankiResult = await ankiResponse.json()
            if (ankiResult.error) {
                throw new Error(`AnkiConnect Error: ${ankiResult.error}`)
            }
            return new Response(JSON.stringify({ success: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        throw new Error(`Unknown action: ${action}`)

    } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        })
    }
})
