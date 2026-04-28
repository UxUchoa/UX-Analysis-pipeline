"""
Data processing utilities for UX Analysis Pipeline.
Extracted from the Streamlit dashboard for reuse by the FastAPI backend.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(value: str) -> str:
    """Remove accents, lowercase, strip."""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def clean_display_text(value: Any, fallback: str = "N/A") -> str:
    """Return user-facing text without leaking pandas null markers."""
    if pd.isna(value):
        return fallback
    text = str(value).strip()
    if not text or normalize_text(text) in {"nan", "none", "null", "n/a", "na"}:
        return fallback
    return text


def clean_team_label(value: Any, fallback: str = "Não informado") -> str:
    """Normalize team/department answers into chart-friendly labels."""
    text = clean_display_text(value, fallback)
    if text == fallback:
        return fallback

    text = re.sub(r"(?i)\bmin[:\s]*\d{1,3}(?::\d{2})?\s*-?\s*", "", text).strip()
    normalized = normalize_text(text)

    team_match = re.search(r"\b(gprom|gecap|gcap)\s*(\d+)?\b", normalized)
    if team_match:
        prefix = team_match.group(1).upper()
        number = team_match.group(2)
        return f"{prefix} {number}" if number else prefix

    if "scheduling" in normalized or "schedul" in normalized:
        return "Equipe de scheduling"

    return text


def clean_gender_label(value: Any, fallback: str = "Não informado") -> str:
    """Normalize participant sex/gender answers into chart-friendly labels."""
    text = clean_display_text(value, fallback)
    if text == fallback:
        return fallback

    normalized = normalize_text(text)
    if normalized in {"m", "masc", "masculino", "homem"}:
        return "Masculino"
    if normalized in {"f", "fem", "feminino", "mulher"}:
        return "Feminino"
    if "nao bin" in normalized:
        return "Não binário"
    if "prefiro nao" in normalized or "nao informar" in normalized:
        return fallback
    return text


def is_valid_interview_row(row: pd.Series, participant_col: str) -> bool:
    """Return False for script/continuation rows and interviews not performed."""
    participant = clean_display_text(row.get(participant_col), "")
    if not participant:
        return False

    row_text = " ".join(
        normalize_text(str(value))
        for value in row.dropna().tolist()
        if clean_display_text(value, "")
    )
    if "entrevista nao realizada" in row_text or "entrevista nao realizado" in row_text:
        return False

    return True


def filter_valid_interview_rows(df: pd.DataFrame, participant_col: str) -> pd.DataFrame:
    """Keep only rows that represent completed participant interviews."""
    if participant_col not in df.columns:
        return df
    mask = df.apply(lambda row: is_valid_interview_row(row, participant_col), axis=1)
    return df[mask].copy()


def short_question_label(question: str, max_len: int = 62) -> str:
    first_line = str(question).splitlines()[0].strip()
    if len(first_line) <= max_len:
        return first_line
    return first_line[: max_len - 3] + "..."


def find_column_by_keywords(columns: list[str], keywords: list[str]) -> str | None:
    normalized = [(col, normalize_text(col)) for col in columns]
    for keyword in keywords:
        for col, col_norm in normalized:
            if keyword in col_norm:
                return col
    return None


def extract_first_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _minutes_from_match(match: re.Match[str], minute_group: int = 1, second_group: int = 2) -> float:
    return int(match.group(minute_group)) + int(match.group(second_group)) / 60


def extract_time_range_minutes(text: object) -> tuple[float | None, float | None]:
    """Extract start/end minute marks from moderator notes."""
    if pd.isna(text):
        return None, None

    raw_text = str(text)
    range_match = re.search(
        r"min\s*in[ií]cio[:\s]*(\d{1,3}):(\d{2})\s*-\s*min\s*fim[:\s]*(\d{1,3}):(\d{2})",
        raw_text,
        re.IGNORECASE,
    )
    if range_match:
        return _minutes_from_match(range_match, 1, 2), _minutes_from_match(range_match, 3, 4)

    single_match = re.search(r"\bmin[:\s]*(\d{1,3}):(\d{2})", raw_text, re.IGNORECASE)
    if single_match:
        value = _minutes_from_match(single_match)
        return value, None

    single_minute_match = re.search(r"\bmin[:\s]*(\d{1,3})\b", raw_text, re.IGNORECASE)
    if single_minute_match:
        return float(single_minute_match.group(1)), None

    return None, None


def extract_time_minutes(text: str) -> float | None:
    """Extract duration in minutes, or a single timestamp when no end mark exists."""
    start_min, end_min = extract_time_range_minutes(text)
    if start_min is not None and end_min is not None:
        return round(max(end_min - start_min, 0), 2)
    return start_min


def strip_time_markers(value: object) -> str:
    """Remove moderation timestamps so status classification uses only the answer."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = re.sub(
        r"min\s*in[ií]cio[:\s]*\d{1,3}:\d{2}\s*-\s*min\s*fim[:\s]*\d{1,3}:\d{2}",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bmin[:\s]*\d{1,3}(?::\d{2})?", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def is_metadata_column(column: object) -> bool:
    """Identify participant/profile columns that should not be treated as tasks."""
    normalized = normalize_text(str(column))
    return (
        normalized in {
            "#",
            "nome",
            "idade",
            "sexo",
            "genero",
            "sexo/genero",
            "sexo genero",
            "gerencia",
        }
        or ("responsavel" in normalized and "tabulacao" in normalized)
    )


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_qualitative_response(value: object) -> str:
    if pd.isna(value):
        return "Sem resposta"

    raw_text = strip_time_markers(value)
    if not raw_text:
        return "Sem resposta"

    text = normalize_text(raw_text)

    if (
        text in {"x", "-"}
        or text.startswith("x -")
        or "nao realizada" in text
        or "nao realizado" in text
        or "nao foi possivel realizar" in text
    ):
        return "Nao realizado"

    if (
        "com facilidade" in text
        or "realizado com sucesso" in text
        or "realizou com sucesso" in text
        or "feito com sucesso" in text
        or "feito com facilidade" in text
        or "realizado com facilidade" in text
        or "achou com facilidade" in text
        or "sem dificuldade" in text
        or "sem problemas" in text
        or "encontrou rapidamente" in text
        or "foi direto" in text
        or "direto ao local correto" in text
        or "configurou corretamente" in text
        or "selecionou corretamente" in text
        or "preencheu corretamente" in text
        or "processo claro" in text
        or "processo simples" in text
    ):
        return "Com facilidade"

    if (
        "dificuldade" in text
        or "demorou" in text
        or "confuso" in text
        or "nao encontrou" in text
        or "nao e obvio" in text
        or "nao ficou claro" in text
        or "te dificuldade" in text
        or "teve dificuldade" in text
        or "dificuldade inicial" in text
        or "lento" in text
        or "lenta" in text
        or "falhou" in text
        or "faltou" in text
        or "precisou ser guiado" in text
        or "nao entendi" in text
        or "duvida" in text
        or "nao tenho a minima ideia" in text
    ):
        return "Com dificuldade"

    if (
        "sucesso" in text
        or "feito" in text
        or "ok" in text
        or text.startswith("sim")
        or "suficiente" in text
        or "esta bom" in text
        or "esta boa" in text
    ):
        return "Concluido"

    return "Comentario aberto"


def detect_dataset_type(df: pd.DataFrame, metadata_cols: list[str]) -> str:
    """Return 'usability', 'context', or 'generic'."""
    cols = [c for c in df.columns if c not in metadata_cols]
    col_texts = [normalize_text(c) for c in cols]
    all_text = " ".join(col_texts)

    context_kw = [
        "idade", "quanto tempo", "gerencia", "equipe", "escala de 1 a 5",
        "atua hoje", "dores", "desafios", "ferramenta", "funcao atual",
        "responsabilidade", "confiante",
    ]
    context_hits = sum(1 for kw in context_kw if kw in all_text)

    usability_kw = [
        "missao", "mostre", "selecione", "busque", "explorar",
        "caminho", "criar", "editar", "desativar", "excluir",
        "ativacao", "bloco", "tela inicial", "confirma",
    ]
    usability_hits = sum(1 for kw in usability_kw if kw in all_text)

    if usability_hits >= 3:
        return "usability"
    if context_hits >= 3:
        return "context"
    long_headers = sum(1 for c in cols if len(str(c)) > 50)
    if long_headers >= 5:
        return "usability"
    return "generic"


# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------

def clean_loaded_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    unnamed = [c for c in cleaned.columns if str(c).startswith("Unnamed")]
    if unnamed:
        cleaned = cleaned.drop(columns=unnamed)

    null_tokens = {"", "nan", "none", "null", "n/a", "na"}
    object_cols = cleaned.select_dtypes(include=["object", "string"]).columns
    for col in object_cols:
        cleaned[col] = cleaned[col].apply(
            lambda v: str(v).strip() if pd.notna(v) else v
        )
        cleaned[col] = cleaned[col].apply(
            lambda v: None if pd.notna(v) and normalize_text(str(v)) in null_tokens else v
        )

    cleaned = cleaned.dropna(axis=0, how="all")
    cleaned = cleaned.dropna(axis=1, how="all")
    return cleaned


def get_metadata_cols(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if is_metadata_column(col)]


# ---------------------------------------------------------------------------
# Usability panel data
# ---------------------------------------------------------------------------

def build_usability_data(df: pd.DataFrame, participant_col: str, question_cols: list[str]) -> list[dict]:
    """Build classification records for the usability panel."""
    records = []
    for _, row in df.iterrows():
        pname = str(row.get(participant_col, "Participante")).strip() or "Participante"
        for q in question_cols:
            val = row.get(q)
            start_min, end_min = extract_time_range_minutes(val)
            records.append({
                "participant": pname,
                "question": q,
                "question_short": short_question_label(q),
                "status": classify_qualitative_response(val),
                "comment": strip_time_markers(val),
                "time_start_min": start_min,
                "time_end_min": end_min,
                "time_min": extract_time_minutes(val),
            })
    return records


def build_value_distribution(values: list[Any], limit: int = 12) -> list[dict]:
    """Return chart-friendly counts for categorical values."""
    series = pd.Series([clean_display_text(value, "") for value in values])
    series = series[series.astype(bool)]
    counts = series.value_counts().head(limit)
    return [{"name": str(name), "count": int(count)} for name, count in counts.items()]


def build_usability_categorical_summary(
    df: pd.DataFrame,
    participant_col: str,
    records: list[dict],
) -> dict:
    """Build useful categorical distributions for usability tests."""
    cols = list(df.columns)
    gender_col = find_column_by_keywords(cols, ["sexo", "genero", "identidade de genero"])
    team_col = find_column_by_keywords(cols, ["gerencia", "equipe"])
    age_col = find_column_by_keywords(cols, ["idade"])

    profile: dict[str, list[dict]] = {}
    if gender_col:
        profile["Sexo/Gênero"] = build_value_distribution(
            [clean_gender_label(value) for value in df[gender_col].tolist()]
        )
    if team_col:
        profile["Gerência/Equipe"] = build_value_distribution(
            [clean_team_label(value) for value in df[team_col].tolist()]
        )
    if age_col:
        bands = []
        for value in df[age_col].tolist():
            age = extract_first_number(value)
            if age is None:
                bands.append("Não informado")
            elif age < 30:
                bands.append("Até 29")
            elif age < 40:
                bands.append("30-39")
            elif age < 50:
                bands.append("40-49")
            else:
                bands.append("50+")
        profile["Faixa etária"] = build_value_distribution(bands)

    status_counts = build_value_distribution([record["status"] for record in records])

    by_participant: dict[str, dict[str, Any]] = {}
    for record in records:
        participant = clean_display_text(record.get("participant"), "Participante")
        row = by_participant.setdefault(
            participant,
            {"participant": participant, "success": 0, "difficulty": 0, "not_completed": 0, "open": 0},
        )
        status = record.get("status")
        if status in {"Com facilidade", "Concluido"}:
            row["success"] += 1
        elif status == "Com dificuldade":
            row["difficulty"] += 1
        elif status == "Nao realizado":
            row["not_completed"] += 1
        else:
            row["open"] += 1

    participant_summary = sorted(
        by_participant.values(),
        key=lambda row: (row["difficulty"] + row["not_completed"], row["open"]),
        reverse=True,
    )

    return {
        "profile": profile,
        "status_distribution": status_counts,
        "participant_summary": participant_summary,
        "participant_col": participant_col,
    }


# ---------------------------------------------------------------------------
# Context panel data
# ---------------------------------------------------------------------------

def build_context_profile(df: pd.DataFrame, participant_col: str) -> tuple[list[dict], dict]:
    """Build profile rows and detected columns for context interviews."""
    cols = list(df.columns)
    age_col = find_column_by_keywords(cols, ["idade"])
    bb_time_col = find_column_by_keywords(cols, [
        "quanto tempo voce trabalha", "tempo trabalha no bb",
        "anos de casa", "ha quanto tempo voce trabalha",
    ])
    gender_col = find_column_by_keywords(cols, [
        "sexo", "genero", "identidade de genero", "identidade genero",
    ])
    team_col = find_column_by_keywords(cols, ["gerencia", "equipe", "atua hoje"])
    team_time_col = find_column_by_keywords(cols, [
        "quanto tempo esta nessa equipe", "tempo esta nessa",
    ])

    profile_rows = []
    for _, row in df.iterrows():
        profile_rows.append({
            "participant": clean_display_text(row.get(participant_col, ""), "Participante"),
            "age": extract_first_number(row.get(age_col)) if age_col else None,
            "gender": clean_gender_label(row.get(gender_col, "")) if gender_col else None,
            "time_bb": extract_first_number(row.get(bb_time_col)) if bb_time_col else None,
            "team": clean_team_label(row.get(team_col, "")) if team_col else "Não informado",
            "time_team": extract_first_number(row.get(team_time_col)) if team_time_col else None,
        })

    detected_cols = {
        "age_col": age_col,
        "gender_col": gender_col,
        "bb_time_col": bb_time_col,
        "team_col": team_col,
        "team_time_col": team_time_col,
    }
    return profile_rows, detected_cols


def build_ratings_data(
    df: pd.DataFrame,
    participant_col: str,
    question_cols: list[str],
) -> list[dict]:
    """Extract numeric ratings from scale-of-1-to-5 columns."""
    note_cols = [
        c for c in question_cols
        if "escala de 1 a 5" in normalize_text(c) or "1 a 5" in normalize_text(c)
    ]
    records = []
    for _, row in df.iterrows():
        pn = str(row.get(participant_col, "")).strip() or "Participante"
        for nc in note_cols:
            sc = extract_first_number(row.get(nc))
            if sc is not None:
                records.append({
                    "participant": pn,
                    "question": short_question_label(nc, 40),
                    "rating": int(round(min(max(sc, 1), 5))),
                })
    return records


# ---------------------------------------------------------------------------
# Theme ranking
# ---------------------------------------------------------------------------

THEME_KEYWORDS = {
    "Confianca": ["confianca", "seguro", "inseguro", "receio", "medo"],
    "Monitoramento": ["monitoramento", "monitoracao", "acompanhamento", "painel", "visibilidade", "grafana"],
    "Dificuldade": [
        "dificuldade", "duvida", "nao entendi", "complexo", "dificil", "nao sei",
        "demorou", "confuso", "falha", "lento", "lenta",
    ],
    "Rastreabilidade": ["rastreabilidade", "rastro", "historico", "consulta", "lastro", "logs"],
    "Automacao": ["automacao", "automatizado", "pipeline", "deploy", "rollback", "ci/cd"],
    "Integracao": ["integracao", "slack", "teams", "jira", "email", "api"],
    "Treinamento": ["treinamento", "documentacao", "workshop", "tutorial", "certificacao"],
    "Performance": ["performance", "velocidade", "rapido", "rapida", "lentidao"],
}


def build_theme_ranking(df: pd.DataFrame, question_cols: list[str], exclude_cols: list[str] | None = None) -> list[dict]:
    """Rank recurring themes in open-text columns."""
    exclude = set(exclude_cols or [])
    open_cols = [c for c in question_cols if c not in exclude and c is not None]

    theme_counts: dict[str, int] = {theme: 0 for theme in THEME_KEYWORDS}
    total_texts = 0

    for _, row in df.iterrows():
        for q in open_cols:
            response = row.get(q)
            if pd.isna(response):
                continue
            text = normalize_text(strip_time_markers(response))
            if not text or text in {"x", "-", "nan"}:
                continue
            total_texts += 1
            for theme, keywords in THEME_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    theme_counts[theme] += 1

    result = []
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        result.append({
            "theme": theme,
            "occurrences": count,
            "percentage": round(count / total_texts * 100, 1) if total_texts else 0.0,
        })
    return result
