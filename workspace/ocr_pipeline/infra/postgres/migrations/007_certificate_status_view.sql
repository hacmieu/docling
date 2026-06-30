-- Filterable certificate / staff document view (metadata-first search).

CREATE OR REPLACE VIEW document_certificate_status AS
SELECT
    d.id AS document_id,
    d.owncloud_path,
    e.extraction_id,
    e.doc_type,
    e.category,
    e.tags,
    COALESCE(e.key_fields->>'ten', e.key_fields->>'ho_ten') AS ten,
    e.key_fields->>'so' AS so_chung_chi,
    e.key_fields->>'ngay_cap' AS ngay_cap,
    e.key_fields->>'ngay_het_han' AS ngay_het_han_raw,
    CASE
        WHEN e.key_fields->>'ngay_het_han' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
            THEN (e.key_fields->>'ngay_het_han')::date
        WHEN e.key_fields->>'ngay_het_han' ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}'
            THEN to_date(e.key_fields->>'ngay_het_han', 'DD/MM/YYYY')
        ELSE NULL
    END AS ngay_het_han,
    e.key_fields->>'pham_vi' AS pham_vi,
    ext.enrich_model,
    e.extracted_summary
FROM documents d
JOIN effective_document_extractions e ON e.document_id = d.id
JOIN document_extractions ext ON ext.id = e.extraction_id
WHERE e.doc_type LIKE 'chung-chi%'
   OR e.tags::text ILIKE '%chung-chi%';

COMMENT ON VIEW document_certificate_status IS
    'Staff certificates with parsed expiry for compliance filters.';
