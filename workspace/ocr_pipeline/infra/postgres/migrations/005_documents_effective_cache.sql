-- Cache effective extraction (priority waterfall) on documents for fast search/sync.

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS effective_extraction_id INTEGER REFERENCES document_extractions(id),
    ADD COLUMN IF NOT EXISTS effective_source_type TEXT,
    ADD COLUMN IF NOT EXISTS effective_priority INTEGER;

CREATE INDEX IF NOT EXISTS idx_documents_effective_source
    ON documents(effective_source_type);
CREATE INDEX IF NOT EXISTS idx_documents_effective_priority
    ON documents(effective_priority DESC);
