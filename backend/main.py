"""
FastAPI backend for UX Analysis Pipeline.
Serves the React frontend with REST endpoints for data upload,
AI analysis, and export.
"""

from __future__ import annotations

import io
import sys
import tempfile
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ux_excel_analyzer import UXExcelAnalyzer
from ux_insights_engine import analyze_excel_data
from backend.data_processing import (
    clean_loaded_dataframe,
    detect_dataset_type,
    get_metadata_cols,
    normalize_text,
    filter_valid_interview_rows,
    find_column_by_keywords,
    build_usability_data,
    build_usability_categorical_summary,
    build_context_profile,
    build_ratings_data,
    build_theme_ranking,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UX Analysis Pipeline API",
    description="REST API for UX data analysis with local LLM",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory state (single-user, local-only)
# ---------------------------------------------------------------------------
_state: dict[str, Any] = {
    "df": None,
    "report": None,
    "dataset_type": "generic",
    "filename": None,
}

_analyzer = UXExcelAnalyzer(model_name="qwen2.5")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class NumpyEncoder:
    """Convert numpy types to Python-native for JSON serialization."""
    @staticmethod
    def convert(obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if pd.isna(obj):
            return None
        return obj


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts with numpy-safe values."""
    records = df.to_dict(orient="records")
    for row in records:
        for k, v in row.items():
            row[k] = NumpyEncoder.convert(v)
    return records


def _get_participant_col(df: pd.DataFrame) -> str:
    lower_cols = {col.lower(): col for col in df.columns}
    name_col = lower_cols.get("nome")
    return name_col if name_col else df.columns[0]


def _get_question_cols(df: pd.DataFrame, metadata_cols: list[str]) -> list[str]:
    return [c for c in df.columns if c not in metadata_cols]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Health check — tests Ollama connection."""
    ollama_ok = _analyzer.client is not None
    return {
        "status": "ok",
        "ollama_connected": ollama_ok,
        "model": _analyzer.model_name,
    }


@app.websocket("/ws")
async def websocket_status(websocket: WebSocket):
    """Accept local preview WebSocket probes without logging 403 errors."""
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            if message.get("text") == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and parse an Excel or CSV file."""
    filename = file.filename.lower()
    content = await file.read()

    try:
        if filename.endswith((".xlsx", ".xls")):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            df = _analyzer.load_excel(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)
            df = clean_loaded_dataframe(df)
        elif filename.endswith(".csv"):
            df = _try_parse_csv(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use .xlsx, .xls, or .csv")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {exc}")

    metadata_cols = get_metadata_cols(df)
    dataset_type = detect_dataset_type(df, metadata_cols)
    participant_col = _get_participant_col(df)
    analysis_df = filter_valid_interview_rows(df, participant_col) if dataset_type == "context" else df

    _state["df"] = analysis_df
    _state["filename"] = file.filename
    _state["report"] = None
    _state["dataset_type"] = dataset_type

    numeric_cols = [c for c in analysis_df.select_dtypes(include=["number"]).columns if c not in metadata_cols]
    cat_cols = [c for c in analysis_df.select_dtypes(include=["object", "category", "bool"]).columns if c not in metadata_cols]

    # Build summary statistics
    describe_df = analysis_df.describe(include="all")
    summary_data = df_to_records(describe_df.reset_index().rename(columns={"index": "statistic"}))

    return {
        "success": True,
        "filename": file.filename,
        "rows": len(analysis_df),
        "raw_rows": len(df),
        "excluded_rows": len(df) - len(analysis_df),
        "columns": len(analysis_df.columns),
        "column_names": list(analysis_df.columns),
        "data_types": {col: str(dtype) for col, dtype in analysis_df.dtypes.items()},
        "dataset_type": dataset_type,
        "numeric_cols": numeric_cols,
        "cat_cols": cat_cols,
        "data": df_to_records(analysis_df),
        "summary": summary_data,
    }


def _try_parse_csv(content: bytes) -> pd.DataFrame:
    """Try multiple CSV parsing strategies and return the best result."""
    parse_attempts = [
        {"sep": ";", "encoding": "utf-8-sig", "engine": "python"},
        {"sep": ";", "encoding": "cp1252", "engine": "python"},
        {"sep": ";", "encoding": "latin1", "engine": "python"},
        {"sep": ",", "encoding": "utf-8-sig", "engine": "python"},
        {"sep": ",", "encoding": "cp1252", "engine": "python"},
        {"sep": ",", "encoding": "latin1", "engine": "python"},
    ]

    best_df: pd.DataFrame | None = None
    best_score = -1
    last_error = None

    for params in parse_attempts:
        try:
            parsed_df = pd.read_csv(
                io.BytesIO(content),
                quotechar='"',
                on_bad_lines="skip",
                **params,
            )
            col_score = parsed_df.shape[1] * 100
            fill_score = int(parsed_df.notna().sum().sum())
            score = col_score + fill_score
            if score > best_score:
                best_score = score
                best_df = parsed_df
        except Exception as exc:
            last_error = exc

    if best_df is not None:
        return clean_loaded_dataframe(best_df)
    raise ValueError(f"Could not parse CSV file. Last error: {last_error}")


@app.post("/api/analyze")
async def analyze_data(context: str = Form("")):
    """Run AI analysis on the uploaded data."""
    if _state["df"] is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Upload a file first.")

    report = _analyzer.analyze_data(_state["df"], context_info=context)
    if report is None:
        raise HTTPException(status_code=500, detail="Analysis failed. Check Ollama service.")

    _state["report"] = report

    return {
        "success": True,
        "summary": report.summary,
        "overall_score": report.overall_score,
        "key_insights": [
            {
                "category": i.category,
                "finding": i.finding,
                "evidence": i.evidence,
                "severity": i.severity,
                "recommendation": i.recommendation,
            }
            for i in report.key_insights
        ],
        "anomalies": report.anomalies,
        "timestamp": report.analysis_timestamp,
    }


@app.get("/api/visualizations")
async def get_visualization_data(dataset_type: str | None = None):
    """Return pre-processed data for the visualization panels."""
    if _state["df"] is None:
        raise HTTPException(status_code=400, detail="No data uploaded.")

    df = _state["df"]
    ds_type = dataset_type or _state["dataset_type"]
    metadata_cols = get_metadata_cols(df)
    participant_col = _get_participant_col(df)
    question_cols = _get_question_cols(df, metadata_cols)
    numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c not in metadata_cols]
    cat_cols = [c for c in df.select_dtypes(include=["object", "category", "bool"]).columns if c not in metadata_cols]

    result: dict[str, Any] = {
        "dataset_type": ds_type,
        "participant_col": participant_col,
    }

    if ds_type == "usability":
        usability_records = build_usability_data(df, participant_col, question_cols)
        result["usability"] = usability_records
        result["question_cols"] = question_cols
        result["usability_categorical"] = build_usability_categorical_summary(
            df,
            participant_col,
            usability_records,
        )

    elif ds_type == "context":
        valid_df = filter_valid_interview_rows(df, participant_col)
        profile_rows, detected_cols = build_context_profile(valid_df, participant_col)
        ratings = build_ratings_data(valid_df, participant_col, question_cols)
        exclude_cols = [v for v in detected_cols.values() if v is not None]
        # Also exclude rating columns
        note_cols = [
            c for c in question_cols
            if "escala de 1 a 5" in normalize_text(c) or "1 a 5" in normalize_text(c)
        ]
        themes = build_theme_ranking(valid_df, question_cols, exclude_cols + note_cols)
        result["context"] = {
            "profiles": profile_rows,
            "detected_cols": {k: v for k, v in detected_cols.items() if v is not None},
            "ratings": ratings,
            "themes": themes,
        }

    # Quantitative data (always include for fallback)
    if numeric_cols:
        quant: dict[str, Any] = {}
        for col in numeric_cols[:6]:
            values = df[col].dropna().tolist()
            quant[col] = {
                "values": [NumpyEncoder.convert(v) for v in values],
                "mean": NumpyEncoder.convert(df[col].mean()),
                "min": NumpyEncoder.convert(df[col].min()),
                "max": NumpyEncoder.convert(df[col].max()),
                "median": NumpyEncoder.convert(df[col].median()),
            }
        result["quantitative"] = {"numeric": quant}

    if cat_cols and ds_type != "usability":
        cat_dist: dict[str, list[dict]] = {}
        categorical_limit = 12 if ds_type == "generic" else 8
        for col in cat_cols[:categorical_limit]:
            counts = df[col].value_counts().head(15)
            cat_dist[col] = [{"name": str(k), "count": int(v)} for k, v in counts.items()]
        if "quantitative" not in result:
            result["quantitative"] = {}
        result["quantitative"]["categorical"] = cat_dist

    return result


@app.get("/api/export/csv")
async def export_csv():
    """Export uploaded data as CSV."""
    if _state["df"] is None:
        raise HTTPException(status_code=400, detail="No data uploaded.")

    csv_data = _state["df"].to_csv(index=False)
    return StreamingResponse(
        io.BytesIO(csv_data.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ux_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"},
    )


@app.get("/api/export/excel")
async def export_excel():
    """Export uploaded data as Excel."""
    if _state["df"] is None:
        raise HTTPException(status_code=400, detail="No data uploaded.")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _state["df"].to_excel(writer, index=False)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=ux_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"},
    )


@app.get("/api/export/report")
async def export_report():
    """Export AI analysis report as JSON."""
    if _state["report"] is None:
        raise HTTPException(status_code=400, detail="No analysis report available. Run analysis first.")

    return JSONResponse(
        content=_state["report"].model_dump(),
        headers={"Content-Disposition": f"attachment; filename=ux_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"},
    )
