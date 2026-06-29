-- Effective metadata per document: highest priority tier available (waterfall), not "active" flag alone.

CREATE OR REPLACE VIEW effective_document_extractions AS
SELECT DISTINCT ON (e.document_id)
    e.document_id,
    e.id AS extraction_id,
    e.source_type,
    e.priority_score,
    e.version_status,
    e.category,
    e.doc_type,
    e.tags,
    e.key_fields,
    e.extracted_summary,
    e.raw_text,
    e.updated_at AS extraction_updated_at
FROM document_extractions e
WHERE e.version_status NOT IN ('archived', 'superseded')
ORDER BY e.document_id, e.priority_score DESC, e.updated_at DESC, e.id DESC;
