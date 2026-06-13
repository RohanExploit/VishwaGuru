-- 🚀 VishwaGuru Supabase Database Schema
-- Run this in your Supabase SQL Editor

-- 1. Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create ENUMs for strict categorization
CREATE TYPE issue_category AS ENUM (
    'pothole', 'garbage', 'streetlight', 'water_leak',
    'abandoned_vehicle', 'vandalism', 'noise', 'other'
);

CREATE TYPE issue_status AS ENUM (
    'pending', 'in_progress', 'resolved', 'rejected'
);

CREATE TYPE issue_priority AS ENUM (
    'low', 'medium', 'high', 'critical'
);

-- 3. Create main civic_reports table
CREATE TABLE civic_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    category issue_category NOT NULL DEFAULT 'other',
    status issue_status NOT NULL DEFAULT 'pending',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    image_url TEXT,
    priority issue_priority NOT NULL DEFAULT 'low',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create report_comments table for community engagement
CREATE TABLE report_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES civic_reports(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create report_votes table for upvoting/downvoting
CREATE TABLE report_votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES civic_reports(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    vote_type SMALLINT NOT NULL CHECK (vote_type IN (1, -1)), -- 1 for upvote, -1 for downvote
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(report_id, user_id) -- Prevent multiple votes by same user on same report
);

-- 6. Setup Row Level Security (RLS)
ALTER TABLE civic_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_votes ENABLE ROW LEVEL SECURITY;

-- Civic Reports Policies
CREATE POLICY "Anyone can view reports" ON civic_reports
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create reports" ON civic_reports
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own reports" ON civic_reports
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reports" ON civic_reports
    FOR DELETE USING (auth.uid() = user_id);

-- Comments Policies
CREATE POLICY "Anyone can view comments" ON report_comments
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create comments" ON report_comments
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own comments" ON report_comments
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own comments" ON report_comments
    FOR DELETE USING (auth.uid() = user_id);

-- Votes Policies
CREATE POLICY "Anyone can view votes" ON report_votes
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can vote" ON report_votes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can change their vote" ON report_votes
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can remove their vote" ON report_votes
    FOR DELETE USING (auth.uid() = user_id);

-- 7. Add Indexes for Performance
CREATE INDEX idx_civic_reports_category ON civic_reports(category);
CREATE INDEX idx_civic_reports_status ON civic_reports(status);
CREATE INDEX idx_civic_reports_created_at ON civic_reports(created_at DESC);
CREATE INDEX idx_civic_reports_location ON civic_reports(latitude, longitude);
CREATE INDEX idx_comments_report_id ON report_comments(report_id);
CREATE INDEX idx_votes_report_id ON report_votes(report_id);

-- 8. Functions & Triggers
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_civic_reports_modtime
    BEFORE UPDATE ON civic_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_report_comments_modtime
    BEFORE UPDATE ON report_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
