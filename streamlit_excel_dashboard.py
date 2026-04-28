#!/usr/bin/env python3
"""
Streamlit dashboard for UX Excel data analysis with local LLM.
"""

from __future__ import annotations

import io
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure local imports work regardless of launch path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ux_excel_analyzer import UXExcelAnalyzer

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "PT": {
        "page_title": "Analisador Excel UX com IA",
        "description": "Faça upload de dados de teste de usabilidade em formato Excel e gere insights de IA locais.",
        "upload_header": "Upload de Dados",
        "upload_help": "Escolha um arquivo de dados (.xlsx, .csv)",
        "upload_success": "Arquivo carregado com sucesso.",
        "upload_error": "Erro ao carregar arquivo: ",
        "upload_prompt": "Faça upload de um arquivo Excel para começar.",
        "analysis_header": "Configurações de Análise",
        "context_label": "Contexto (opcional):",
        "context_placeholder": "Exemplo: Testando novo fluxo de checkout",
        "analyze_btn": "Analisar com IA",
        "analyzing_spinner": "Analisando dados com modelo local...",
        "analysis_success": "Análise concluída.",
        "analysis_error": "Falha na análise. Verifique o serviço Ollama e o modelo.",
        "tab_overview": "Visão Geral dos Dados",
        "tab_insights": "Insights da IA",
        "tab_visualizations": "Visualizações",
        "tab_export": "Exportar",
        "total_records": "Total de Registros",
        "columns": "Colunas",
        "data_types": "Tipos de Dados",
        "raw_data": "Dados Brutos",
        "summary": "Resumo",
        "run_analyze_prompt": "Execute 'Analisar com IA' na barra lateral para gerar insights.",
        "overall_score": "Pontuação Geral",
        "exec_summary": "Resumo Executivo",
        "key_insights": "Principais Insights",
        "anomalies": "Anomalias e Outliers",
        "finding": "Descoberta",
        "evidence": "Evidência",
        "severity": "Severidade",
        "recommendation": "Recomendação",
        "vis_ux_tab": "Testes de Usabilidade",
        "vis_context_tab": "Entrevistas de Contexto",
        "vis_quant_tab": "Análises Quantitativas",
        "panel_title": "Painel de Execução das Tarefas (Roteiro UX)",
        "panel_desc": "Classificação automática das respostas por tarefa para facilitar leitura da planilha qualitativa.",
        "task_dist_title": "Distribuição de status por tarefa",
        "task_axis": "Tarefa",
        "qty_responses": "Quantidade de respostas",
        "detail_task": "Detalhar respostas da tarefa",
        "participant": "Participante",
        "status": "Status",
        "context_interview_title": "Entrevista de Contexto",
        "participants_metric": "Participantes",
        "avg_age_metric": "Idade média",
        "avg_time_metric": "Tempo médio BB (anos)",
        "not_informed": "Não informado",
        "qty": "Quantidade",
        "team_dist_title": "Distribuição por equipe/gerência",
        "notes_dist_title": "Distribuição de notas (1 a 5)",
        "notes_by_question": "Notas por pergunta",
        "no_numeric_answers": "Não foram encontradas respostas numéricas para as perguntas de nota.",
        "theme_rank_title": "Ranking de temas recorrentes",
        "themes_chart_title": "Temas mais citados nas respostas",
        "cat_dist_title": "Distribuições Categóricas",
        "dist_of": "Distribuição de",
        "corr_heatmap_title": "Mapa de Calor de Correlação",
        "corr_caption": "Valores de correlação variam de -1 a 1. Esta escala não é a escala da métrica bruta.",
        "corr_explorer_title": "Explorador de Correlação",
        "corr_select": "Selecione uma métrica para inspecionar correlações",
        "corr_slider": "Correlação absoluta mínima para exibir",
        "no_corr": "Sem correlações acima do limite selecionado.",
        "corr_with": "Correlações com",
        "download_csv": "Baixar Dados (CSV)",
        "download_excel": "Baixar Dados (Excel)",
        "download_json": "Baixar Relatório (JSON)",
    },
    "EN": {
        "page_title": "UX Excel Analyzer with AI",
        "description": "Upload usability testing data in Excel format and generate local AI insights.",
        "upload_header": "Upload Data",
        "upload_help": "Choose a data file (.xlsx, .csv)",
        "upload_success": "File loaded successfully.",
        "upload_error": "Error loading file: ",
        "upload_prompt": "Upload an Excel file to get started.",
        "analysis_header": "Analysis Settings",
        "context_label": "Context (optional):",
        "context_placeholder": "Example: Testing new checkout flow",
        "analyze_btn": "Analyze with AI",
        "analyzing_spinner": "Analyzing data with local model...",
        "analysis_success": "Analysis complete.",
        "analysis_error": "Analysis failed. Check Ollama service and model.",
        "tab_overview": "Data Overview",
        "tab_insights": "AI Insights",
        "tab_visualizations": "Visualizations",
        "tab_export": "Export",
        "total_records": "Total Records",
        "columns": "Columns",
        "data_types": "Data Types",
        "raw_data": "Raw Data",
        "summary": "Summary",
        "run_analyze_prompt": "Run 'Analyze with AI' in the sidebar to generate insights.",
        "overall_score": "Overall Score",
        "exec_summary": "Executive Summary",
        "key_insights": "Key Insights",
        "anomalies": "Anomalies and Outliers",
        "finding": "Finding",
        "evidence": "Evidence",
        "severity": "Severity",
        "recommendation": "Recommendation",
        "vis_ux_tab": "Usability Tests",
        "vis_context_tab": "Context Interviews",
        "vis_quant_tab": "Quantitative Analysis",
        "panel_title": "Task Execution Panel (UX Script)",
        "panel_desc": "Automatic classification of responses by task to facilitate qualitative sheet reading.",
        "task_dist_title": "Status distribution by task",
        "task_axis": "Task",
        "qty_responses": "Quantity of responses",
        "detail_task": "Detail task responses",
        "participant": "Participant",
        "status": "Status",
        "context_interview_title": "Context Interview",
        "participants_metric": "Participants",
        "avg_age_metric": "Average Age",
        "avg_time_metric": "Avg Time (years)",
        "not_informed": "Not informed",
        "qty": "Quantity",
        "team_dist_title": "Distribution by team/area",
        "notes_dist_title": "Rating distribution (1 to 5)",
        "notes_by_question": "Ratings by question",
        "no_numeric_answers": "No numeric answers found for rating questions.",
        "theme_rank_title": "Recurring themes ranking",
        "themes_chart_title": "Most cited themes in responses",
        "cat_dist_title": "Categorical Distributions",
        "dist_of": "Distribution of",
        "corr_heatmap_title": "Correlation Heatmap",
        "corr_caption": "Correlation values range from -1 to 1. This scale is not the raw metric scale.",
        "corr_explorer_title": "Correlation Explorer",
        "corr_select": "Select a metric to inspect correlations",
        "corr_slider": "Minimum absolute correlation to show",
        "no_corr": "No correlations above the selected threshold.",
        "corr_with": "Correlations with",
        "download_csv": "Download Data (CSV)",
        "download_excel": "Download Data (Excel)",
        "download_json": "Download Report (JSON)",
    }
}


st.set_page_config(
    page_title="UX Excel Analyzer",
    page_icon="U",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .insight-card {
        background-color: #f8f9fa;
        color: #111827 !important;
        padding: 15px;
        border-left: 4px solid #007bff;
        border-radius: 5px;
        margin: 10px 0;
    }
    .insight-card h4,
    .insight-card p,
    .insight-card strong,
    .insight-card span {
        color: #111827 !important;
    }
    .critical { border-left-color: #dc3545; }
    .high { border-left-color: #fd7e14; }
    .medium { border-left-color: #17a2b8; }
    .low { border-left-color: #28a745; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Language Selection
selected_lang = st.sidebar.radio("Language / Idioma", ["PT", "EN"], index=0, horizontal=True)
t = TRANSLATIONS[selected_lang]


if "analyzer" not in st.session_state:
    st.session_state.analyzer = UXExcelAnalyzer(model_name="qwen2.5")
if "df" not in st.session_state:
    st.session_state.df = None
if "report" not in st.session_state:
    st.session_state.report = None


def render_insight_card(insight, severity_class: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card {severity_class}">
            <h4>{insight.category}</h4>
            <p><strong>{t['finding']}:</strong> {insight.finding}</p>
            <p><strong>{t['evidence']}:</strong> {insight.evidence}</p>
            <p><strong>{t['severity']}:</strong> {insight.severity}</p>
            {"<p><strong>" + t['recommendation'] + ":</strong> " + insight.recommendation + "</p>" if insight.recommendation else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def classify_qualitative_response(value: object) -> str:
    if pd.isna(value):
        return "Sem resposta"

    raw_text = str(value).strip()
    if not raw_text:
        return "Sem resposta"

    text = normalize_text(raw_text)

    if text in {"x", "-"} or "nao realizada" in text or "nao realizado" in text:
        return "Nao realizado"

    if (
        "dificuldade" in text
        or "precisou ser guiado" in text
        or "nao entendi" in text
        or "duvida" in text
        or "nao tenho a minima ideia" in text
    ):
        return "Com dificuldade"

    if (
        "com facilidade" in text
        or "realizado com sucesso" in text
        or "realizou com sucesso" in text
        or "feito com sucesso" in text
        or "realizado com facilidade" in text
        or "achou com facilidade" in text
    ):
        return "Com facilidade"

    if "sucesso" in text or "feito" in text or "ok" in text:
        return "Concluido"

    return "Comentario aberto"


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


def build_theme_ranking(qual_df: pd.DataFrame) -> pd.DataFrame:
    theme_keywords = {
        "Confianca": ["confianca", "seguro", "inseguro", "receio", "medo"],
        "Monitoramento": ["monitoramento", "monitoracao", "acompanhamento", "painel", "visibilidade"],
        "Dificuldade": ["dificuldade", "duvida", "nao entendi", "complexo", "dificil", "nao sei"],
        "Rastreabilidade": ["rastreabilidade", "rastro", "historico", "consulta", "lastro"],
    }
    theme_counts = {theme: 0 for theme in theme_keywords}
    total_texts = 0

    for response in qual_df["response_text"]:
        if pd.isna(response):
            continue
        text = normalize_text(str(response))
        if not text or text in {"x", "-", "nan"}:
            continue
        total_texts += 1
        for theme, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords):
                theme_counts[theme] += 1

    rank_df = pd.DataFrame(
        [{"tema": theme, "ocorrencias": count, "percentual": (count / total_texts * 100) if total_texts else 0.0} for theme, count in theme_counts.items()]
    ).sort_values("ocorrencias", ascending=False)
    return rank_df


def load_uploaded_dataframe(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()

    if filename.endswith((".xlsx", ".xls")):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        df = st.session_state.analyzer.load_excel(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        return clean_loaded_dataframe(df)

    if filename.endswith(".csv"):
        parse_attempts = [
            {"sep": ";", "encoding": "utf-8-sig", "engine": "python"},
            {"sep": ";", "encoding": "cp1252", "engine": "python"},
            {"sep": ";", "encoding": "latin1", "engine": "python"},
            {"sep": ",", "encoding": "utf-8-sig", "engine": "python"},
            {"sep": ",", "encoding": "cp1252", "engine": "python"},
            {"sep": ",", "encoding": "latin1", "engine": "python"},
        ]

        last_error = None
        best_df: pd.DataFrame | None = None
        best_score = -1
        for params in parse_attempts:
            try:
                uploaded_file.seek(0)
                parsed_df = pd.read_csv(
                    uploaded_file,
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

    raise ValueError("Unsupported file type. Use .xlsx, .xls, or .csv")


def clean_loaded_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    # Drop auto-generated empty columns from CSV parsing
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


def detect_dataset_type(df: pd.DataFrame, metadata_cols: list[str]) -> str:
    """Return 'usability', 'context', or 'generic'."""
    cols = [c for c in df.columns if c not in metadata_cols]
    col_texts = [normalize_text(c) for c in cols]
    all_text = " ".join(col_texts)

    # Context interview signals: age, time at bank, team questions, rating scales
    context_kw = ["idade", "quanto tempo", "gerencia", "equipe", "escala de 1 a 5",
                   "atua hoje", "dores", "desafios", "ferramenta", "funcao atual",
                   "responsabilidade", "confiante"]
    context_hits = sum(1 for kw in context_kw if kw in all_text)

    # Usability test signals: task-oriented action verbs
    usability_kw = ["missao", "mostre", "selecione", "busque", "explorar",
                     "caminho", "criar", "editar", "desativar", "excluir",
                     "ativacao", "bloco", "tela inicial", "confirma"]
    usability_hits = sum(1 for kw in usability_kw if kw in all_text)

    # Context check FIRST (it also has long headers but has distinct profile questions)
    if context_hits >= 3:
        return "context"
    if usability_hits >= 3:
        return "usability"
    # Fallback: many long headers = usability-like
    long_headers = sum(1 for c in cols if len(str(c)) > 50)
    if long_headers >= 5:
        return "usability"
    return "generic"


def extract_time_minutes(text: str) -> float | None:
    """Extract time in minutes from text like 'Min 1:34' or 'Min: 18:04'."""
    if pd.isna(text):
        return None
    match = re.search(r"[Mm]in[:\s]*(\d{1,3}):(\d{2})", str(text))
    if match:
        return int(match.group(1)) + int(match.group(2)) / 60
    match2 = re.search(r"[Mm]in[:\s]*(\d{1,3})", str(text))
    if match2:
        return float(match2.group(1))
    return None


def render_tab_usability(df, participant_col, question_cols):
    """Render Usability Tests: success rate, heatmap, time, team, age."""
    if len(question_cols) < 3:
        st.info("Dados insuficientes para o painel de usabilidade.")
        return

    # --- Build classification data ---
    records = []
    for _, row in df.iterrows():
        pname = str(row.get(participant_col, "Participante")).strip() or "Participante"
        for q in question_cols:
            val = row.get(q)
            records.append({
                "participant": pname,
                "question": q,
                "question_short": short_question_label(q),
                "status": classify_qualitative_response(val),
                "time_min": extract_time_minutes(val),
            })
    qual_df = pd.DataFrame(records)

    status_order = ["Com facilidade", "Concluido", "Com dificuldade",
                    "Nao realizado", "Comentario aberto", "Sem resposta"]
    color_map = {"Com facilidade": "#2ca02c", "Concluido": "#1f77b4",
                 "Com dificuldade": "#ff7f0e", "Nao realizado": "#d62728",
                 "Comentario aberto": "#9467bd", "Sem resposta": "#7f7f7f"}

    # --- 1) Taxa de Sucesso por Tarefa ---
    st.subheader("📊 Taxa de Sucesso por Tarefa")
    st.caption("Percentual de participantes que completaram cada tarefa com ou sem dificuldade.")
    summary = qual_df.groupby(["question_short", "status"], as_index=False).size().rename(columns={"size": "count"})
    summary["status"] = pd.Categorical(summary["status"], categories=status_order, ordered=True)
    total_per_q = summary.groupby("question_short")["count"].transform("sum")
    summary["pct"] = (summary["count"] / total_per_q * 100).round(1)
    fig = px.bar(summary.sort_values("status"), x="question_short", y="pct", color="status",
                 barmode="stack", color_discrete_map=color_map,
                 category_orders={"status": status_order},
                 labels={"pct": "%", "question_short": "Tarefa"})
    fig.update_layout(yaxis_title="% dos participantes", xaxis_title="Tarefa")
    st.plotly_chart(fig, width="stretch")

    # Success rate metrics
    success_statuses = {"Com facilidade", "Concluido"}
    total = len(qual_df)
    successes = len(qual_df[qual_df["status"].isin(success_statuses)])
    difficulties = len(qual_df[qual_df["status"] == "Com dificuldade"])
    failures = len(qual_df[qual_df["status"] == "Nao realizado"])
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("Taxa de Sucesso Geral", f"{successes/total*100:.0f}%" if total else "N/A")
    with mc2:
        st.metric("Com Dificuldade", f"{difficulties/total*100:.0f}%" if total else "N/A")
    with mc3:
        st.metric("Não Realizado", f"{failures/total*100:.0f}%" if total else "N/A")

    # --- 2) Heatmap Participante × Tarefa ---
    st.subheader("🗺️ Heatmap Participante × Tarefa")
    status_num = {"Com facilidade": 4, "Concluido": 3, "Com dificuldade": 2,
                  "Nao realizado": 1, "Comentario aberto": 0, "Sem resposta": -1}
    qual_df["status_num"] = qual_df["status"].map(status_num)
    pivot = qual_df.pivot_table(index="participant", columns="question_short",
                                values="status_num", aggfunc="first")
    pivot_labels = qual_df.pivot_table(index="participant", columns="question_short",
                                       values="status", aggfunc="first")
    fig_hm = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        text=pivot_labels.values, texttemplate="%{text}",
        colorscale=[[0, "#7f7f7f"], [0.25, "#d62728"], [0.5, "#ff7f0e"],
                    [0.75, "#1f77b4"], [1.0, "#2ca02c"]],
        showscale=False,
    ))
    fig_hm.update_layout(height=max(300, len(pivot) * 45), xaxis_title="Tarefa", yaxis_title="Participante")
    st.plotly_chart(fig_hm, width="stretch")

    # --- 3) Tempo de Realização (extraído do texto) ---
    time_data = qual_df.dropna(subset=["time_min"])
    if not time_data.empty:
        st.subheader("⏱️ Tempo de Realização por Tarefa")
        st.caption("Tempos extraídos automaticamente das anotações (ex: 'Min 1:34').")
        fig_time = px.box(time_data, x="question_short", y="time_min",
                          labels={"time_min": "Minutos", "question_short": "Tarefa"},
                          points="all")
        fig_time.update_layout(xaxis_title="Tarefa", yaxis_title="Tempo (min)")
        st.plotly_chart(fig_time, width="stretch")

    # --- 4) Gerência e Idade (se existirem como colunas) ---
    all_cols = list(df.columns)
    age_col = find_column_by_keywords(all_cols, ["idade"])
    team_col = find_column_by_keywords(all_cols, ["gerencia", "equipe", "atua hoje", "area"])

    if age_col or team_col:
        st.subheader("👥 Perfil da Amostra")
        cols_m = st.columns(2 if age_col and team_col else 1)
        ci = 0
        if age_col:
            with cols_m[ci]:
                ages = df[age_col].apply(extract_first_number).dropna()
                if not ages.empty:
                    st.metric("Idade Média", f"{ages.mean():.1f} anos")
                    st.plotly_chart(px.histogram(ages, nbins=10, title="Distribuição de Idade",
                                                labels={"value": "Idade", "count": "Qtd"}), width="stretch")
            ci += 1
        if team_col:
            with cols_m[ci]:
                teams = df[team_col].fillna("Não informado").value_counts().reset_index()
                teams.columns = ["Equipe", "Qtd"]
                st.plotly_chart(px.pie(teams, values="Qtd", names="Equipe",
                                      title="Distribuição por Gerência"), width="stretch")

    # --- 5) Índice de Dificuldade ---
    st.subheader("🔴 Índice de Dificuldade por Tarefa")
    diff_statuses = {"Com dificuldade", "Nao realizado"}
    diff_df = qual_df.groupby("question_short").apply(
        lambda g: pd.Series({
            "dificuldade_pct": len(g[g["status"].isin(diff_statuses)]) / len(g) * 100,
            "total": len(g),
        })
    ).reset_index().sort_values("dificuldade_pct", ascending=True)
    fig_diff = px.bar(diff_df, x="dificuldade_pct", y="question_short", orientation="h",
                      labels={"dificuldade_pct": "% Dificuldade/Falha", "question_short": "Tarefa"},
                      color="dificuldade_pct", color_continuous_scale=["#2ca02c", "#ff7f0e", "#d62728"])
    fig_diff.update_layout(yaxis_title="", showlegend=False)
    st.plotly_chart(fig_diff, width="stretch")

    # --- 6) Detalhamento por tarefa ---
    st.subheader("🔍 Detalhamento por Tarefa")
    sel_q = st.selectbox("Selecione a tarefa", options=question_cols,
                         format_func=short_question_label, key="qual_question_selector")
    sel_rows = qual_df[qual_df["question"] == sel_q]
    st.dataframe(sel_rows[["participant", "status"]].rename(
        columns={"participant": "Participante", "status": "Status"}),
        width="stretch", hide_index=True)


def render_tab_context(df, participant_col, question_cols):
    """Render Context Interviews: time at BB, topics, team, age, ratings."""
    st.subheader("📋 " + t["context_interview_title"])

    age_col = find_column_by_keywords(list(df.columns), ["idade"])
    bb_time_col = find_column_by_keywords(list(df.columns),
        ["quanto tempo voce trabalha", "tempo trabalha no bb", "anos de casa",
         "ha quanto tempo voce trabalha"])
    team_col = find_column_by_keywords(list(df.columns),
        ["gerencia", "equipe", "atua hoje"])
    team_time_col = find_column_by_keywords(list(df.columns),
        ["quanto tempo esta nessa equipe", "tempo esta nessa"])

    # --- Build profile ---
    profile_rows = []
    for _, row in df.iterrows():
        profile_rows.append({
            "Participante": str(row.get(participant_col, "")).strip() or "Participante",
            "Idade": extract_first_number(row.get(age_col)) if age_col else None,
            "Tempo_BB": extract_first_number(row.get(bb_time_col)) if bb_time_col else None,
            "Equipe": str(row.get(team_col, "")).strip() if team_col else "N/A",
            "Tempo_Equipe": extract_first_number(row.get(team_time_col)) if team_time_col else None,
        })
    profile_df = pd.DataFrame(profile_rows)

    # --- Metrics ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Participantes", int(profile_df["Participante"].nunique()))
    with m2:
        avg_age = profile_df["Idade"].dropna().mean()
        st.metric("Idade Média", f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A")
    with m3:
        avg_bb = profile_df["Tempo_BB"].dropna().mean()
        st.metric("Tempo Médio BB (anos)", f"{avg_bb:.1f}" if pd.notna(avg_bb) else "N/A")
    with m4:
        avg_te = profile_df["Tempo_Equipe"].dropna().mean()
        st.metric("Tempo Médio Equipe (anos)", f"{avg_te:.1f}" if pd.notna(avg_te) else "N/A")

    # --- Age + Time histograms ---
    c1, c2 = st.columns(2)
    with c1:
        ages = profile_df["Idade"].dropna()
        if not ages.empty:
            st.plotly_chart(px.histogram(ages, nbins=8, title="Distribuição de Idade",
                                        labels={"value": "Idade", "count": "Qtd"}), width="stretch")
    with c2:
        times = profile_df["Tempo_BB"].dropna()
        if not times.empty:
            st.plotly_chart(px.histogram(times, nbins=8, title="Tempo de Atuação no Banco",
                                        labels={"value": "Anos", "count": "Qtd"}), width="stretch")

    # --- Team distribution ---
    if team_col:
        st.subheader("🏢 Distribuição por Gerência")
        teams = profile_df["Equipe"].fillna("N/A").replace("", "N/A").value_counts().reset_index()
        teams.columns = ["Equipe", "Qtd"]
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(teams, values="Qtd", names="Equipe",
                                  title="Participantes por Gerência"), width="stretch")
        with c2:
            st.plotly_chart(px.bar(teams, x="Equipe", y="Qtd",
                                  title="Qtd por Gerência"), width="stretch")

    # --- Ratings (1-5 scale) ---
    note_cols = [c for c in question_cols
                 if "escala de 1 a 5" in normalize_text(c) or "1 a 5" in normalize_text(c)]
    if note_cols:
        st.subheader("⭐ Notas de Satisfação (1 a 5)")
        nrecs = []
        for _, row in df.iterrows():
            pn = str(row.get(participant_col, "")).strip() or "Participante"
            for nc in note_cols:
                sc = extract_first_number(row.get(nc))
                if sc is not None:
                    nrecs.append({"Participante": pn, "Pergunta": short_question_label(nc, 40),
                                  "Nota": int(round(min(max(sc, 1), 5)))})
        if nrecs:
            ndf = pd.DataFrame(nrecs)
            avg_per_q = ndf.groupby("Pergunta")["Nota"].mean().reset_index()
            avg_per_q.columns = ["Pergunta", "Média"]
            st.dataframe(avg_per_q.style.format({"Média": "{:.1f}"}), width="stretch", hide_index=True)
            nc2 = ndf.groupby(["Pergunta", "Nota"], as_index=False).size().rename(columns={"size": "Qtd"})
            st.plotly_chart(px.bar(nc2, x="Nota", y="Qtd", color="Pergunta", barmode="group",
                                  category_orders={"Nota": [1, 2, 3, 4, 5]},
                                  title="Distribuição de Notas"), width="stretch")

    # --- Topics ranking ---
    st.subheader("💬 Tópicos Mais Mencionados")
    open_cols = [c for c in question_cols if c not in (
        [age_col, bb_time_col, team_col, team_time_col] + note_cols)]
    open_cols = [c for c in open_cols if c is not None]
    if open_cols:
        qual_text_df = pd.DataFrame([{"response_text": row.get(q)}
                                     for _, row in df.iterrows() for q in open_cols])
        theme_rank_df = build_theme_ranking(qual_text_df)
        fig_th = px.bar(theme_rank_df, x="ocorrencias", y="tema", orientation="h",
                        text="percentual", title="Temas Recorrentes nas Respostas",
                        color="ocorrencias", color_continuous_scale="Blues")
        fig_th.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_th.update_layout(yaxis_title="", showlegend=False)
        st.plotly_chart(fig_th, width="stretch")
        st.dataframe(theme_rank_df, width="stretch", hide_index=True)


def render_tab_quantitative(df, numeric_cols, cat_cols):
    """Render Quantitative Analysis (generic fallback)."""
    if not numeric_cols and not cat_cols:
        st.info("Nenhum dado quantitativo encontrado.")
        return
    if numeric_cols:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.histogram(df, x=numeric_cols[0], nbins=20,
                                        title=f"Distribuição de {numeric_cols[0]}"), width="stretch")
        with c2:
            bm = st.selectbox("Box plot", options=numeric_cols, index=0, key="box_metric_selector")
            st.plotly_chart(px.box(df, y=bm, points="outliers", title=f"Box Plot - {bm}"), width="stretch")
    if cat_cols:
        st.subheader("Distribuições Categóricas")
        for col in cat_cols[:3]:
            cdf = df[col].value_counts().rename_axis(col).reset_index(name="count")
            st.plotly_chart(px.bar(cdf, x=col, y="count", title=f"Distribuição de {col}"), width="stretch")


def main() -> None:
    st.title(t["page_title"])
    st.markdown(t["description"])

    st.sidebar.header(t["upload_header"])
    uploaded_file = st.sidebar.file_uploader(t["upload_help"], type=["xlsx", "xls", "csv"])

    if uploaded_file is not None:
        try:
            st.session_state.df = load_uploaded_dataframe(uploaded_file)
            st.sidebar.success(t["upload_success"])
        except Exception as exc:
            st.sidebar.error(f"{t['upload_error']}{exc}")
            return

    if st.session_state.df is None:
        st.info(t["upload_prompt"])
        return

    st.sidebar.header(t["analysis_header"])
    context_info = st.sidebar.text_area(t["context_label"], placeholder=t["context_placeholder"], height=80)

    if st.sidebar.button(t["analyze_btn"], key="analyze_btn"):
        with st.spinner(t["analyzing_spinner"]):
            st.session_state.report = st.session_state.analyzer.analyze_data(st.session_state.df, context_info=context_info)
        if st.session_state.report:
            st.sidebar.success(t["analysis_success"])
        else:
            st.sidebar.error(t["analysis_error"])

    tab1, tab2, tab3, tab4 = st.tabs([t["tab_overview"], t["tab_insights"], t["tab_visualizations"], t["tab_export"]])

    # --- Tab 1: Data Overview ---
    with tab1:
        st.header(t["tab_overview"])
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(t["total_records"], len(st.session_state.df))
        with c2:
            st.metric(t["columns"], len(st.session_state.df.columns))
        with c3:
            st.metric(t["data_types"], len(st.session_state.df.dtypes.unique()))
        st.subheader(t["raw_data"])
        st.dataframe(st.session_state.df, width="stretch")
        st.subheader(t["summary"])
        st.write(st.session_state.df.describe(include="all"))

    # --- Tab 2: AI Insights ---
    with tab2:
        st.header(t["tab_insights"])
        if st.session_state.report is None:
            st.info(t["run_analyze_prompt"])
        else:
            st.metric(t["overall_score"], f"{st.session_state.report.overall_score}/10")
            st.subheader(t["exec_summary"])
            st.info(st.session_state.report.summary)
            st.subheader(t["key_insights"])
            for insight in st.session_state.report.key_insights:
                render_insight_card(insight, insight.severity.lower())
            if st.session_state.report.anomalies:
                st.subheader(t["anomalies"])
                for anomaly in st.session_state.report.anomalies:
                    st.warning(anomaly)

    # --- Tab 3: Visualizations (dynamic) ---
    with tab3:
        st.header(t["tab_visualizations"])
        df = st.session_state.df.copy()

        lower_cols = {col.lower(): col for col in df.columns}
        name_col = lower_cols.get("nome")
        participant_col = name_col if name_col else df.columns[0]
        metadata_cols = [
            col for col in df.columns
            if normalize_text(col) in {"#", "nome"}
            or "responsavel" in normalize_text(col)
            or "tabulacao" in normalize_text(col)
        ]
        numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c not in metadata_cols]
        cat_cols = [c for c in df.select_dtypes(include=["object", "category", "bool"]).columns if c not in metadata_cols]
        question_cols = [c for c in df.columns if c not in metadata_cols]

        auto_type = detect_dataset_type(df, metadata_cols)
        type_labels = {
            "auto": f"🔍 Automático ({auto_type})",
            "usability": "🧪 Teste de Usabilidade",
            "context": "🎙️ Entrevista de Contexto",
            "generic": "📊 Genérico / Quantitativo",
        }
        selected_type = st.sidebar.selectbox(
            "Tipo de Visualização",
            options=list(type_labels.keys()),
            format_func=lambda k: type_labels[k],
            index=0,
            key="ds_type_override",
        )
        ds_type = auto_type if selected_type == "auto" else selected_type

        if ds_type == "usability":
            render_tab_usability(df, participant_col, question_cols)
        elif ds_type == "context":
            render_tab_context(df, participant_col, question_cols)
        else:
            render_tab_quantitative(df, numeric_cols, cat_cols)

    # --- Tab 4: Export ---
    with tab4:
        st.header(t["tab_export"])
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                label=t["download_csv"],
                data=st.session_state.df.to_csv(index=False),
                file_name=f"ux_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        with c2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                st.session_state.df.to_excel(writer, index=False)
            buf.seek(0)
            st.download_button(
                label=t["download_excel"],
                data=buf.getvalue(),
                file_name=f"ux_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with c3:
            if st.session_state.report is not None:
                st.download_button(
                    label=t["download_json"],
                    data=st.session_state.report.model_dump_json(indent=2),
                    file_name=f"ux_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )


if __name__ == "__main__":
    main()

