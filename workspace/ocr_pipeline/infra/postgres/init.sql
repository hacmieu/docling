-- OCR pipeline catalog schema (PostgreSQL SoT target)

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    owncloud_path TEXT UNIQUE,
    local_path TEXT,
    source_path TEXT,
    source_sha256 TEXT NOT NULL,
    markdown TEXT NOT NULL DEFAULT '',
    doc_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    ai_review TEXT,
    ai_review_status TEXT,
    ai_review_at TIMESTAMPTZ,
    ai_review_model TEXT,
    ai_review_error TEXT,
    ai_doc_type TEXT,
    ai_category TEXT,
    ai_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_key_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    ai_ocr_quality TEXT,
    verified_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    verified_at TIMESTAMPTZ,
    verified_source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_owncloud_path ON documents(owncloud_path);
CREATE INDEX IF NOT EXISTS idx_documents_ai_category ON documents(ai_category);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_markdown_fts ON documents
    USING gin (to_tsvector('simple', coalesce(markdown, '')));
