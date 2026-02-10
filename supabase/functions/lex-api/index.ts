import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-environment',
    'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
}

serve(async (req) => {
    // Handle CORS
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const authHeader = req.headers.get('Authorization')

        const envHeader = req.headers.get('X-Environment')
        const targetSchema = envHeader === 'mock' ? 'lex_mock' : 'lex'

        // Use service role key for DB operations (bypasses RLS)
        const supabaseClient = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        // For auth verification
        const supabaseAuth = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        )

        const url = new URL(req.url)
        const path = url.pathname.split('/lex-api')[1] || '/'
        const method = req.method

        // Verify authentication for non-GET requests
        if (method !== 'GET') {
            const token = authHeader?.replace('Bearer ', '')
            if (!token) {
                return new Response(JSON.stringify({ error: 'Missing Authorization header' }), {
                    status: 401,
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
            const { data: { user }, error: authError } = await supabaseAuth.auth.getUser(token)
            if (authError || !user) {
                return new Response(JSON.stringify({ error: 'Unauthorized', details: authError?.message }), {
                    status: 401,
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        // Simple routing logic
        if (path === '/' || path === '/api_status') {
            return new Response(JSON.stringify({ api_status: 'working' }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path === '/learn/overview' && method === 'GET') {
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_learn_overview')
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data: sources, error: err } = await supabaseClient
                    .from(`${targetSchema}.source`)
                    .select(`
                        id, 
                        title, 
                        author, 
                        word_count,
                        lemma_source (
                            first_position,
                            lemma (
                                status_id
                            )
                        )
                    `)

                if (err) throw err

                const result = (sources || []).map((s: any) => {
                    const lemmata = s.lemma_source || []
                    return {
                        id: s.id,
                        title: s.title,
                        author: s.author,
                        word_count: s.word_count,
                        new_count: lemmata.filter((ls: any) => ls.lemma?.status_id === 1).length,
                        learning_count: lemmata.filter((ls: any) => ls.lemma?.status_id === 2).length,
                        learned_count: lemmata.filter((ls: any) => ls.lemma?.status_id === 3).length,
                        max_learned_position: Math.max(0, ...lemmata.filter((ls: any) => ls.lemma?.status_id === 3).map((ls: any) => ls.first_position || 0))
                    }
                })

                return new Response(JSON.stringify(result), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        // Lemma endpoints
        if (path === '/check_duplicate' && method === 'POST') {
            const { lemma } = await req.json()
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('check_mock_duplicate', { p_lemma: lemma })
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.lemma`)
                    .select('id, lemma')
                    .eq('lemma', lemma)
                    .maybeSingle()

                if (error) throw error
                return new Response(JSON.stringify({ exists: !!data, ...data }), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path.startsWith('/lemma/') && method === 'GET') {
            const id = path.split('/')[2]
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_lemma', { p_lemma_id: parseInt(id) })
                if (error) throw error
                return new Response(JSON.stringify(data || {}), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.lemma`)
                    .select('*')
                    .eq('id', id)
                    .single()

                if (error) throw error
                return new Response(JSON.stringify(data || {}), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path === '/lemma' && method === 'PATCH') {
            const { id, lemma } = await req.json()
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('update_mock_lemma', { p_id: id, p_lemma: lemma })
                if (error) throw error
                return new Response(JSON.stringify(true), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { error } = await supabaseClient
                    .from(`${targetSchema}.lemma`)
                    .update({ lemma })
                    .eq('id', id)

                if (error) throw error
                return new Response(JSON.stringify(true), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path === '/lemma' && method === 'DELETE') {
            const lemma_ids: number[] = await req.json()
            console.log(`[DELETE /lemma] Processing ${lemma_ids.length} lemmata.`)

            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('delete_mock_lemmata', { p_ids: lemma_ids })
                if (error) throw error
                return new Response(JSON.stringify(true), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                for (const id of lemma_ids) {
                    try {
                        // 1. Get lemma data
                        const { data: lemma, error: lemmaError } = await supabaseClient
                            .from(`${targetSchema}.lemma`)
                            .select('found_in_source')
                            .eq('id', id)
                            .single()

                        if (lemmaError || !lemma) {
                            console.log(`[DELETE /lemma] Lemma ${id} not found, skipping.`)
                            continue
                        }

                        // 2. Process associated contexts
                        const { data: links, error: linksError } = await supabaseClient
                            .from(`${targetSchema}.lemma_context`)
                            .select('context_id')
                            .eq('lemma_id', id)

                        if (linksError) {
                            console.error(`[DELETE /lemma] Error fetching context IDs for lemma ${id}:`, linksError)
                        }

                        const contextIds = (links || []).map(l => l.context_id)

                        for (const cid of contextIds) {
                            // Check for other distinct lemmata associated with this context
                            const { data: allLinks, error: allLinksError } = await supabaseClient
                                .from(`${targetSchema}.lemma_context`)
                                .select('lemma_id')
                                .eq('context_id', cid)

                            if (allLinksError) {
                                console.error(`[DELETE /lemma] Error fetching relationships for context ${cid}:`, allLinksError)
                                continue
                            }

                            const distinctLemmataIds = new Set((allLinks || []).map(l => l.lemma_id))

                            if (distinctLemmataIds.size === 1 && distinctLemmataIds.has(id)) {
                                // Only this lemma is linked here, so we should delete the context entirely
                                console.log(`[DELETE /lemma] Context ${cid} is local to lemma ${id}. Deleting context.`)
                                const { error: ctxDeleteError } = await supabaseClient.from(`${targetSchema}.context`).delete().eq('id', cid)
                                if (ctxDeleteError) console.error(`[DELETE /lemma] Error deleting context ${cid}:`, ctxDeleteError)
                            } else if (distinctLemmataIds.has(id)) {
                                // Context is shared with other lemmata. We must cleanup the text tag for 'id'.
                                console.log(`[DELETE /lemma] Context ${cid} is shared. Removing tag ::${id} from text.`)
                                const { data: context, error: fetchCtxError } = await supabaseClient
                                    .from(`${targetSchema}.context`)
                                    .select('context_value')
                                    .eq('id', cid)
                                    .single()

                                if (!fetchCtxError && context && context.context_value) {
                                    // Pattern: separator :: followed by ID, then a non-digit or end of string.
                                    const regex = new RegExp(`::${id}([^0-9]|$)`, 'g')
                                    const updatedValue = context.context_value.replace(regex, '$1')

                                    if (updatedValue !== context.context_value) {
                                        const { error: updateError } = await supabaseClient
                                            .from(`${targetSchema}.context`)
                                            .update({ context_value: updatedValue })
                                            .eq('id', cid)
                                        if (updateError) console.error(`[DELETE /lemma] Error updating context ${cid}:`, updateError)
                                    }
                                }
                            }

                            // Always delete the specific relation for this (lemma, context) pair
                            await supabaseClient.from(`${targetSchema}.lemma_context`)
                                .delete()
                                .eq('lemma_id', id)
                                .eq('context_id', cid)
                        }

                        // 3. Cleanup relations and update source counter
                        await supabaseClient.from(`${targetSchema}.lemma_source`).delete().eq('lemma_id', id)

                        if (lemma.found_in_source) {
                            const { data: source } = await supabaseClient
                                .from(`${targetSchema}.source`)
                                .select('removed_lemmata_num')
                                .eq('id', lemma.found_in_source)
                                .single()

                            if (source) {
                                await supabaseClient
                                    .from('source')
                                    .update({ removed_lemmata_num: (source.removed_lemmata_num || 0) + 1 })
                                    .eq('id', lemma.found_in_source)
                            }
                        }

                        // 4. Final lemma deletion
                        const { error: finalLemmaDeleteError } = await supabaseClient.from(`${targetSchema}.lemma`).delete().eq('id', id)
                        if (finalLemmaDeleteError) {
                            console.error(`[DELETE /lemma] Error deleting lemma ${id}:`, finalLemmaDeleteError)
                        } else {
                            console.log(`[DELETE /lemma] Successfully deleted lemma ${id}.`)
                        }

                    } catch (lemmaProcessError: any) {
                        console.error(`[DELETE /lemma] Unexpected error on lemma ${id}:`, lemmaProcessError)
                    }
                }

                return new Response(JSON.stringify(true), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path.startsWith('/lemma_status_by_id/') && method === 'GET') {
            const id = path.split('/')[2]
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_lemma_status_by_id', { p_status_id: parseInt(id) })
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.lemma_status`)
                    .select('*')
                    .eq('id', id)
                    .single()

                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        // Lemma status endpoints
        if (path === '/status' && method === 'PATCH') {
            const { lemma_ids, new_status_id } = await req.json()
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('update_mock_status', { p_lemma_ids: lemma_ids, p_new_status_id: new_status_id })
                if (error) throw error
                return new Response(JSON.stringify(true), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { error } = await supabaseClient
                    .from(`${targetSchema}.lemma`)
                    .update({ status_id: new_status_id })
                    .in('id', lemma_ids)

                if (error) throw error
                return new Response(JSON.stringify(true), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path === '/lemma' && method === 'POST') {
            const lemma = await req.json()
            const { data, error } = await supabaseClient
                .from(`${targetSchema}.lemma`)
                .insert(lemma)
                .select('id')
                .single()

            if (error) throw error
            return new Response(JSON.stringify(data.id), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path === '/status_lemmata' && method === 'GET') {
            const status_val = url.searchParams.get('status_val')
            const source_id = url.searchParams.get('source_id')
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')

            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_status_lemmata', {
                    p_status_val: status_val,
                    p_source_id: source_id ? parseInt(source_id) : null,
                    p_page: page,
                    p_page_size: page_size
                })

                if (error) {
                    throw new Error(`RPC Error in schema "${targetSchema}": ${JSON.stringify(error)}`)
                }

                if (data && data.error) {
                    throw new Error(data.error)
                }

                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                let statusId: number | null = null;
                const { data: statusData, error: statusError } = await supabaseClient
                    .from(`${targetSchema}.lemma_status`)
                    .select('id')
                    .eq('status', status_val)
                    .single()

                if (statusError || !statusData) {
                    const { data: allStatuses } = await supabaseClient.from(`${targetSchema}.lemma_status`).select('status')
                    throw new Error(`Status not found: "${status_val}" in schema "${targetSchema}". Error: ${JSON.stringify(statusError)}. Available: ${allStatuses?.map((s: any) => s.status).join(', ')}`)
                }
                statusId = statusData.id;

                const start = (page - 1) * page_size
                const end = start + page_size - 1

                let query = supabaseClient
                    .from(`${targetSchema}.lemma`)
                    .select('*, lemma_source!inner(source_id)')
                    .eq('status_id', statusId)

                if (source_id) {
                    query = query.eq('lemma_source.source_id', source_id)
                }

                const { data, error } = await query
                    .order('id')
                    .range(start, end)

                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path === '/sync_anki_maturity' && method === 'POST') {
            // 1. Get all lemmata in 'learning' status (id: 2)
            const { data: learningLemmata, error: fetchError } = await supabaseClient
                .from(`${targetSchema}.lemma`)
                .select('id, lemma')
                .eq('status_id', 2)

            if (fetchError) throw fetchError

            const ankiConnectUrl = url.origin + '/anki-connect'
            const updatedIds: number[] = []

            for (const l of (learningLemmata || [])) {
                try {
                    // a. Find cards for this lemma
                    const findRes = await fetch(ankiConnectUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: authHeader || '',
                            apikey: Deno.env.get('SUPABASE_ANON_KEY') ?? '',
                            'X-Environment': envHeader || 'lex'
                        },
                        body: JSON.stringify({
                            action: 'findCards',
                            params: { query: `tag:lemma_${l.id}` }
                        })
                    })
                    const findData = await findRes.json()
                    const cardIds = findData.result || []

                    if (cardIds.length > 0) {
                        // b. Get card info
                        const infoRes = await fetch(ankiConnectUrl, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                Authorization: authHeader || '',
                                apikey: Deno.env.get('SUPABASE_ANON_KEY') ?? '',
                                'X-Environment': envHeader || 'lex'
                            },
                            body: JSON.stringify({
                                action: 'cardsInfo',
                                params: { cards: cardIds }
                            })
                        })
                        const infoData = await infoRes.json()
                        const cards = infoData.result || []

                        // c. Check if any card is mature (ivl >= 21)
                        const isMature = cards.some((c: any) => c.ivl >= 21)

                        if (isMature) {
                            // d. Update status in Supabase
                            const { error: updateError } = await supabaseClient
                                .from(`${targetSchema}.lemma`)
                                .update({ status_id: 3 }) // 'learned'
                                .eq('id', l.id)

                            if (!updateError) {
                                updatedIds.push(l.id)
                            }
                        }
                    }
                } catch (e) {
                    console.error(`Error syncing maturity for lemma ${l.id}:`, e)
                }
            }

            return new Response(JSON.stringify({ success: true, updated_count: updatedIds.length, updated_ids: updatedIds }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // Context endpoints
        if (path === '/contexts' && method === 'GET') {
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')

            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_contexts', { p_page: page, p_page_size: page_size })
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const start = (page - 1) * page_size
                const end = start + page_size - 1

                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.context`)
                    .select('*')
                    .order('id')
                    .range(start, end)

                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path.startsWith('/lemma_contexts/') && method === 'GET') {
            const lemma_id = path.replace('/lemma_contexts/', '')
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')

            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_lemma_contexts', {
                    p_lemma_id: parseInt(lemma_id),
                    p_page: page,
                    p_page_size: page_size
                })
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.lemma_context`)
                    .select('context(*)')
                    .eq('lemma_id', lemma_id)
                    .range((page - 1) * page_size, page * page_size - 1)

                if (error) throw error
                return new Response(JSON.stringify((data || []).map((d: any) => d.context)), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        // Source endpoints
        if (path === '/sources' && method === 'GET') {
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')

            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_sources', {
                    p_page: page,
                    p_page_size: page_size,
                    p_author: url.searchParams.get('author') || null,
                    p_lang: url.searchParams.get('lang') || null,
                    p_source_kind_id: url.searchParams.get('source_kind_id') ? parseInt(url.searchParams.get('source_kind_id')!) : null
                })
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                let query = supabaseClient.from(`${targetSchema}.source`).select('*')

                const author = url.searchParams.get('author')
                const lang = url.searchParams.get('lang')
                const source_kind_id = url.searchParams.get('source_kind_id')

                if (author) query = query.eq('author', author)
                if (lang) query = query.eq('lang', lang)
                if (source_kind_id) query = query.eq('source_kind_id', source_kind_id)

                const { data, error } = await query
                    .order('id')
                    .range((page - 1) * page_size, page * page_size - 1)

                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path.startsWith('/source/') && method === 'GET') {
            const id = path.split('/')[2]
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_source', { p_source_id: parseInt(id) })
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.source`)
                    .select('*')
                    .eq('id', id)
                    .single()
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        // Other POST endpoints
        if (method === 'POST') {
            const body = await req.json()

            // 1. Mock Schema Routing (Consolidated RPC Bridges)
            if (targetSchema === 'lex_mock') {
                const bulkPaths = ['/bulk_lemma_source', '/bulk_lemma_context', '/bulk_lemmata', '/bulk_lemma_derivation', '/lemma_derivations/search']
                if (bulkPaths.includes(path)) {
                    const { data, error } = await supabaseClient.rpc('mock_bulk_bridge', { p_path: path, p_body: body })
                    if (error) throw error
                    return new Response(JSON.stringify(data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
                }

                if (path === '/bulk_lemma_ignored') {
                    const { error } = await supabaseClient.rpc('bulk_mock_lemma_ignored', { p_entries: body })
                    if (error) throw error
                    return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
                }

                if (path === '/lemma_derivation') {
                    const { data, error } = await supabaseClient.rpc('create_mock_lemma_derivation', { p_source: body.source, p_target_id: body.target_id })
                    if (error) throw error
                    return new Response(JSON.stringify(data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
                }

                // Fallback for mock singular inserts
                const { data, error } = await supabaseClient.rpc('mock_single_insert_bridge', { p_path: path, p_body: body })
                if (error) throw error
                // Singular bridges return {id: ...} but most production endpoints return just data.id
                return new Response(JSON.stringify(data.id), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }

            // 2. Production Schema Logic (Existing)
            if (path === '/bulk_lemma_source') {
                const { error } = await supabaseClient.from(`${targetSchema}.lemma_source`).insert(body)
                if (error) throw error
                return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            if (path === '/bulk_lemma_context') {
                const { error } = await supabaseClient.from(`${targetSchema}.lemma_context`).insert(body)
                if (error) throw error
                return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            if (path === '/bulk_lemma_ignored') {
                const { error } = await supabaseClient.from(`${targetSchema}.lemma_ignored`).insert(body)
                if (error) throw error
                return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            if (path === '/bulk_lemmata') {
                const { lemmata } = body
                const { data, error } = await supabaseClient.from(`${targetSchema}.lemma`).insert(lemmata).select('id, lemma')
                if (error) throw error
                const result = data.reduce((acc: any, curr: any) => { acc[curr.lemma] = curr.id; return acc }, {})
                return new Response(JSON.stringify(result), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            if (path === '/lemma_derivation') {
                const { data, error } = await supabaseClient.from(`${targetSchema}.lemma_derivation`).insert(body).select('id').single()
                if (error) throw error
                return new Response(JSON.stringify(data.id), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            if (path === '/bulk_lemma_derivation') {
                const { error } = await supabaseClient.from(`${targetSchema}.lemma_derivation`).insert(body)
                if (error) throw error
                return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            if (path === '/lemma_derivations/search') {
                const { sources } = body
                const { data, error } = await supabaseClient.from(`${targetSchema}.lemma_derivation`).select('source, target_id').in('source', sources)
                if (error) throw error
                return new Response(JSON.stringify(data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }

            let table = ''
            if (path === '/lemma_status') table = 'lemma_status'
            else if (path === '/lemma_source') table = 'lemma_source'
            else if (path === '/source_kind') table = 'source_kind'
            else if (path === '/source') table = 'source'
            else if (path === '/context') table = 'context'
            else if (path === '/lemma_context') table = 'lemma_context'
            else if (path === '/lemma') table = 'lemma'
            else throw new Error(`Unknown POST path: ${path}`)

            const { data, error } = await supabaseClient.from(`${targetSchema}.${table}`).insert(body).select('id').single()
            if (error) throw error
            return new Response(JSON.stringify(data.id), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
        }

        // Ignored lemmata list
        if (path === '/lemma_ignored' && method === 'GET') {
            if (targetSchema === 'lex_mock') {
                const { data, error } = await supabaseClient.rpc('get_mock_lemma_ignored')
                if (error) throw error
                return new Response(JSON.stringify(data), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            } else {
                const { data, error } = await supabaseClient
                    .from(`${targetSchema}.lemma_ignored`)
                    .select('lemma')
                if (error) throw error
                return new Response(JSON.stringify(data ? data.map((d: any) => d.lemma) : []), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        return new Response(JSON.stringify({ error: 'Not Found', path, method }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        })

    } catch (error: any) {
        console.error('[UNCAUGHT ERROR]', error)
        return new Response(JSON.stringify({
            error: error.message,
            code: error.code,
            details: error.details,
            hint: error.hint
        }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        })
    }
})
