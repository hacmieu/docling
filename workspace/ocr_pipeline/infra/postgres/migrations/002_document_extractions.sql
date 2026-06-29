-- Multi-version extraction metadata (human > google_vision > deepseek > local OCR)

CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    prompt_body TEXT NOT NULL,
    doc_type_hint TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_extractions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_no INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    priority_score INTEGER NOT NULL,
    version_status TEXT NOT NULL DEFAULT 'draft',
    category TEXT,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    key_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    extracted_summary TEXT,
    raw_text TEXT,
    model_name TEXT,
    prompt_template_id INTEGER REFERENCES prompt_templates(id),
    created_by TEXT,
    teable_record_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version_no),
    CONSTRAINT document_extractions_source_type_check CHECK (
        source_type IN (
            'human_verified',
            'human_webchat',
            'google_vision',
            'deepseek_cleanup',
            'local_llm_ocr'
        )
    ),
    CONSTRAINT document_extractions_version_status_check CHECK (
        version_status IN ('draft', 'active', 'superseded', 'archived')
    )
);

CREATE INDEX IF NOT EXISTS idx_document_extractions_document_id
    ON document_extractions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_extractions_priority
    ON document_extractions(document_id, priority_score DESC, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_extractions_source_type
    ON document_extractions(source_type);
CREATE INDEX IF NOT EXISTS idx_document_extractions_status
    ON document_extractions(version_status);

-- Seed default webchat prompts (idempotent)
INSERT INTO prompt_templates (slug, name, prompt_body, doc_type_hint)
VALUES
    (
        'hop-dong-lao-dong',
        'Hợp đồng lao động',
        'Bóc tách: họ tên, ngày sinh, chức vụ, thời hạn HĐ, mức lương, đơn vị ký. Trả JSON: category, tags, key_fields {ten, so, ngay, don_vi}.',
        'hop-dong'
    ),
    (
        'quyet-dinh',
        'Quyết định',
        'Bóc tách: số QĐ, ngày ban hành, cơ quan ban hành, trích yếu, người được quyết định. Trả JSON chuẩn.',
        'quyet-dinh'
    ),
    (
        'pham-vi-hanh-nghe',
        'Phạm vi hành nghề',
        'Xác định văn bản có liên quan phạm vi hành nghề; trích điều khoản, đối tượng áp dụng, ngày hiệu lực.',
        'quy-dinh'
    )
ON CONFLICT (slug) DO NOTHING;
