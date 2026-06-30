-- Separate OCR model from metadata-enrich model on extractions.

ALTER TABLE document_extractions
    ADD COLUMN IF NOT EXISTS enrich_model TEXT;

COMMENT ON COLUMN document_extractions.model_name IS 'Model that produced raw_text (OCR/ASR/parse).';
COMMENT ON COLUMN document_extractions.enrich_model IS 'Model that produced category/tags/key_fields/summary.';
