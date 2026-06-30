"""Build Docling converters per ingest strategy."""

from __future__ import annotations

import argparse

from workspace.ocr_pipeline.ingest_formats import (
    STRATEGY_ASR,
    STRATEGY_DOCLING_OCR,
    STRATEGY_DOCLING_PARSE,
)


def build_converter_for_strategy(
    strategy: str,
    ocr_args: argparse.Namespace,
) -> object:
    """Return a Docling DocumentConverter appropriate for the ingest strategy."""
    from docling.document_converter import DocumentConverter

    if strategy == STRATEGY_DOCLING_PARSE:
        return DocumentConverter()

    if strategy == STRATEGY_DOCLING_OCR:
        from scripts.folder_to_sqlite_mvp import build_converter

        return build_converter(ocr_args)

    if strategy == STRATEGY_ASR:
        from docling.datamodel import asr_model_specs
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import AsrPipelineOptions
        from docling.document_converter import AudioFormatOption
        from docling.pipeline.asr_pipeline import AsrPipeline

        pipeline_options = AsrPipelineOptions()
        pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO
        return DocumentConverter(
            format_options={
                InputFormat.AUDIO: AudioFormatOption(
                    pipeline_cls=AsrPipeline,
                    pipeline_options=pipeline_options,
                )
            }
        )

    raise ValueError(f"Unsupported ingest strategy for Docling: {strategy}")
