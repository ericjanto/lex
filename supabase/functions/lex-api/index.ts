import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
    // Handle CORS
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const supabaseClient = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_ANON_KEY') ?? '',
            {
                global: { headers: { Authorization: req.headers.get('Authorization')! } },
                db: { schema: 'lex' }
            }
        )

        const url = new URL(req.url)
        const path = url.pathname.replace('/lex-api', '')
        const method = req.method

        // Simple routing logic
        if (path === '/' || path === '/api_status') {
            return new Response(JSON.stringify({ api_status: 'working' }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // Lemma endpoints
        if (path.startsWith('/lemma/') && method === 'GET') {
            const id = path.split('/')[2]
            const { data, error } = await supabaseClient
                .from('lemma')
                .select('*')
                .eq('id', id)
                .single()

            if (error) throw error
            return new Response(JSON.stringify(data || {}), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path === '/lemma' && method === 'DELETE') {
            const lemma_ids: number[] = await req.json()

            for (const id of lemma_ids) {
                // 1. Get lemma data
                const { data: lemma, error: lemmaError } = await supabaseClient
                    .from('lemma')
                    .select('found_in_source')
                    .eq('id', id)
                    .single()

                if (lemmaError) continue

                // 2. Get associated contexts
                const { data: contexts, error: contextsError } = await supabaseClient
                    .from('lemma_context')
                    .select('context_id')
                    .eq('lemma_id', id)

                if (!contextsError && contexts) {
                    for (const c of contexts) {
                        const { data: context, error: contextError } = await supabaseClient
                            .from('context')
                            .select('context_value')
                            .eq('id', c.context_id)
                            .single()

                        if (!contextError && context) {
                            const updatedValue = context.context_value.replace(new RegExp(`::${id}(\\D)`, 'g'), '$1')
                            await supabaseClient
                                .from('context')
                                .update({ context_value: updatedValue })
                                .eq('id', c.context_id)
                        }
                    }
                }

                // 3. Delete relations
                await supabaseClient.from('lemma_context').delete().eq('lemma_id', id)
                await supabaseClient.from('lemma_source').delete().eq('lemma_id', id)

                // 4. Update source counter
                const { data: source } = await supabaseClient
                    .from('source')
                    .select('removed_lemmata_num')
                    .eq('id', lemma.found_in_source)
                    .single()

                if (source) {
                    await supabaseClient
                        .from('source')
                        .update({ removed_lemmata_num: source.removed_lemmata_num + 1 })
                        .eq('id', lemma.found_in_source)
                }

                // 5. Delete lemma
                await supabaseClient.from('lemma').delete().eq('id', id)
            }

            return new Response(JSON.stringify(true), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path === '/status' && method === 'PATCH') {
            const { lemma_ids, new_status_id } = await req.json()
            const { error } = await supabaseClient
                .from('lemma')
                .update({ status_id: new_status_id })
                .in('id', lemma_ids)

            if (error) throw error
            return new Response(JSON.stringify(true), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path === '/lemma' && method === 'POST') {
            const lemma = await req.json()
            const { data, error } = await supabaseClient
                .from('lemma')
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
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')

            // First find status_id
            const { data: statusData } = await supabaseClient
                .from('lemma_status')
                .select('id')
                .eq('status', status_val)
                .single()

            if (!statusData) throw new Error('Status not found')

            const start = (page - 1) * page_size
            const end = start + page_size - 1

            const { data, error } = await supabaseClient
                .from('lemma')
                .select('*')
                .eq('status_id', statusData.id)
                .order('id')
                .range(start, end)

            if (error) throw error
            return new Response(JSON.stringify(data), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // Context endpoints
        if (path === '/contexts' && method === 'GET') {
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')
            const start = (page - 1) * page_size
            const end = start + page_size - 1

            const { data, error } = await supabaseClient
                .from('context')
                .select('*')
                .order('id')
                .range(start, end)

            if (error) throw error
            return new Response(JSON.stringify(data), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path.startsWith('/lemma_contexts/') && method === 'GET') {
            const lemma_id = path.split('/')[2]
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')

            // Join with context table via lemma_context
            const { data, error } = await supabaseClient
                .from('lemma_context')
                .select('context(*)')
                .eq('lemma_id', lemma_id)
                .range((page - 1) * page_size, page * page_size - 1)

            if (error) throw error
            return new Response(JSON.stringify(data.map((d: any) => d.context)), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // Source endpoints
        if (path === '/sources' && method === 'GET') {
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')
            let query = supabaseClient.from('source').select('*')

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

        if (path.startsWith('/source/') && method === 'GET') {
            const id = path.split('/')[2]
            const { data, error } = await supabaseClient
                .from('source')
                .select('*')
                .eq('id', id)
                .single()
            if (error) throw error
            return new Response(JSON.stringify(data), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // POST/PATCH endpoints for other entities
        if (method === 'POST') {
            const body = await req.json()
            let table = ''
            if (path === '/lemma_status') table = 'lemma_status'
            else if (path === '/lemma_source') table = 'lemma_source'
            else if (path === '/source_kind') table = 'source_kind'
            else if (path === '/source') table = 'source'
            else if (path === '/context') table = 'context'
            else if (path === '/lemma_context') table = 'lemma_context'
            else if (path === '/bulk_lemma_source') {
                const { error } = await supabaseClient.from('lemma_source').insert(body)
                if (error) throw error
                return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            else if (path === '/bulk_lemma_context') {
                const { error } = await supabaseClient.from('lemma_context').insert(body)
                if (error) throw error
                return new Response(JSON.stringify(true), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }
            else if (path === '/bulk_lemmata') {
                const { lemmata } = body
                const { data, error } = await supabaseClient.from('lemma').insert(lemmata).select('id, lemma')
                if (error) throw error
                const result = data.reduce((acc: any, curr: any) => { acc[curr.lemma] = curr.id; return acc }, {})
                return new Response(JSON.stringify(result), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
            }

            if (table) {
                const { data, error } = await supabaseClient.from(table).insert(body).select('id').single()
                if (error) throw error
                return new Response(JSON.stringify(data.id), {
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                })
            }
        }

        if (path === '/lemma_id' && method === 'GET') {
            const { value } = await req.json()
            const { data, error } = await supabaseClient
                .from('lemma')
                .select('id')
                .eq('lemma', value)
                .single()
            if (error) throw error
            return new Response(JSON.stringify(data.id), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path.startsWith('/lemma_status/') && method === 'GET') {
            const status_val = path.split('/')[2]
            const { data, error } = await supabaseClient
                .from('lemma_status')
                .select('id')
                .eq('status', status_val)
                .single()
            if (error) throw error
            return new Response(JSON.stringify(data.id), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path.startsWith('/lemma_status_by_id/') && method === 'GET') {
            const status_id = path.split('/')[3]
            const { data, error } = await supabaseClient
                .from('lemma_status')
                .select('*')
                .eq('id', status_id)
                .single()
            if (error) throw error
            return new Response(JSON.stringify(data), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path.startsWith('/source_kind/') && method === 'GET') {
            const id = path.split('/')[2]
            const { data, error } = await supabaseClient
                .from('source_kind')
                .select('*')
                .eq('id', id)
                .single()
            if (error) throw error
            return new Response(JSON.stringify(data), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path.startsWith('/source_contexts/') && method === 'GET') {
            const source_id = path.split('/')[2]
            const page = parseInt(url.searchParams.get('page') ?? '1')
            const page_size = parseInt(url.searchParams.get('page_size') ?? '100')
            const { data, error } = await supabaseClient
                .from('context')
                .select('*')
                .eq('source_id', source_id)
                .order('id')
                .range((page - 1) * page_size, page * page_size - 1)
            if (error) throw error
            return new Response(JSON.stringify(data), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        if (path === '/bulk_lemma' && method === 'GET') {
            const lemmata_values = await req.json()
            const { data, error } = await supabaseClient
                .from('lemma')
                .select('id, lemma')
                .in('lemma', lemmata_values)

            if (error) throw error
            const result = data.reduce((acc: any, curr: any) => {
                acc[curr.lemma] = curr.id
                return acc
            }, {})
            return new Response(JSON.stringify(result), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            })
        }

        // Add more endpoints as needed...
        // For now, return 404 for unhandled paths
        return new Response(JSON.stringify({ error: 'Not Found', path }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        })

    } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        })
    }
})
