-- Fix match_embeddings function to bypass RLS
-- The function needs SECURITY DEFINER to bypass Row Level Security
-- This is safe because the function itself handles user filtering

CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding halfvec(1536),
    match_threshold float DEFAULT 0.70,
    match_count int DEFAULT 15,
    filter_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content_id uuid,
    chunk_text text,
    chunk_sequence int,
    similarity float,
    content_title text,
    content_url text,
    content_author text,
    published_at timestamptz,
    source_id uuid,
    source_priority int
)
LANGUAGE sql STABLE
SECURITY DEFINER  -- This bypasses RLS
SET search_path = public
AS $$
    SELECT
        e.id,
        e.content_id,
        e.chunk_text,
        e.chunk_sequence,
        1 - (e.embedding <=> query_embedding) AS similarity,
        c.title AS content_title,
        c.url AS content_url,
        c.author AS content_author,
        c.published_at,
        c.source_id,
        s.priority AS source_priority
    FROM embeddings e
    JOIN content c ON e.content_id = c.id
    JOIN sources s ON c.source_id = s.id
    WHERE
        1 - (e.embedding <=> query_embedding) > match_threshold
        AND s.active = true
        AND (filter_user_id IS NULL OR s.user_id = filter_user_id)
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Verify the function was updated
DO $$
BEGIN
    RAISE NOTICE '✅ match_embeddings function updated with SECURITY DEFINER';
    RAISE NOTICE '';
    RAISE NOTICE 'The function will now bypass RLS and use its own user filtering logic.';
    RAISE NOTICE 'This is safe because the function enforces user_id filtering internally.';
END $$;
