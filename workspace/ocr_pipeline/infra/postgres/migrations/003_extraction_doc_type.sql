ALTER TABLE document_extractions
    ADD COLUMN IF NOT EXISTS doc_type TEXT;

CREATE INDEX IF NOT EXISTS idx_document_extractions_doc_type
    ON document_extractions(doc_type);
