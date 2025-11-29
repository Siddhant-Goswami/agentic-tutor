-- Research Planner Tables Migration
-- Adds tables for storing research plans and web search results

-- Research plans table
CREATE TABLE IF NOT EXISTS research_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    content_analysis JSONB NOT NULL,
    search_queries JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'denied', 'modified')),
    user_modifications JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Web search results table
CREATE TABLE IF NOT EXISTS web_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    research_plan_id UUID REFERENCES research_plans(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    results JSONB NOT NULL,
    source_api TEXT NOT NULL CHECK (source_api IN ('tavily', 'brave', 'fallback')),
    searched_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_research_plans_session ON research_plans(session_id);
CREATE INDEX IF NOT EXISTS idx_research_plans_user ON research_plans(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_plans_status ON research_plans(status);
CREATE INDEX IF NOT EXISTS idx_web_search_results_session ON web_search_results(session_id);
CREATE INDEX IF NOT EXISTS idx_web_search_results_plan ON web_search_results(research_plan_id);

-- Enable Row Level Security
ALTER TABLE research_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE web_search_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Users can manage their own research plans
CREATE POLICY "Users can manage own research plans"
    ON research_plans FOR ALL
    USING (auth.uid() = user_id);

-- Users can view web search results for their research plans
CREATE POLICY "Users can view own web search results"
    ON web_search_results FOR SELECT
    USING (
        research_plan_id IN (
            SELECT id FROM research_plans WHERE user_id = auth.uid()
        )
    );

-- Users can insert web search results for their research plans
CREATE POLICY "Users can insert own web search results"
    ON web_search_results FOR INSERT
    WITH CHECK (
        research_plan_id IN (
            SELECT id FROM research_plans WHERE user_id = auth.uid()
        )
    );

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Research planner tables created successfully!';
    RAISE NOTICE 'Tables added: research_plans, web_search_results';
    RAISE NOTICE 'Indexes and RLS policies configured';
END $$;
