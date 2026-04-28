# UX Analysis Pipeline

Aplicação local para análise de pesquisas UX a partir de planilhas. O app combina um frontend em React, um backend em FastAPI e análise com LLM local via Ollama para processar testes de usabilidade e mapeamentos de perfil sem enviar dados para serviços externos.

## Funcionalidades

O upload aceita arquivos `.xlsx`, `.xls` e `.csv`. Uma nova tabela pode ser enviada a qualquer momento, mesmo quando já existe um arquivo carregado.

O backend detecta automaticamente o tipo de base:

- **Teste de usabilidade**: planilhas com tarefas, missões, observações por participante e marcações de tempo.
- **Mapeamento de perfil**: entrevistas de contexto com dados demográficos, perguntas abertas e notas em escala.
- **Genérico/quantitativo**: bases tabulares que não seguem os roteiros UX esperados.

### Testes de Usabilidade

- Taxa de sucesso, dificuldade e não realização.
- Índice de dificuldade por tarefa.
- Extração de tempo a partir de marcações como `Min Início` e `Min Fim`.
- Detalhamento por tarefa com participante, status, duração e observação limpa.
- Distribuições úteis para o cenário: status geral, perfil da amostra, faixa etária e participantes com mais fricção.

### Mapeamento de Perfil

- Perfil da amostra por idade, sexo/gênero, gerência/equipe e tempo de experiência.
- Distribuição por gerência/equipe.
- Notas de satisfação/confiança em escala de 1 a 5.
- Ranking de temas recorrentes em respostas abertas.
- Filtragem de linhas que não representam entrevistas realizadas.

### Análise com IA Local

- Geração de resumo executivo, insights, evidências, severidade, anomalias e recomendações.
- Uso do Ollama local com o modelo `qwen2.5`.
- Normalização e fallback para respostas inválidas do LLM.
- Dados processados localmente.

## Arquitetura

```text
React + Vite + Recharts + Lucide
        |
        | HTTP/REST
        v
FastAPI + Pandas + Pydantic
        |
        v
Ollama local - qwen2.5
```

## Pré-requisitos

- Python 3.9+
- Node.js 18+
- Ollama instalado e rodando localmente
- Modelo `qwen2.5` disponível no Ollama

## Instalação

```bash
cd ux_analysis_pipeline

python -m venv .venv
.venv\Scripts\activate

pip install -r backend/requirements.txt

cd frontend
npm install
cd ..

ollama pull qwen2.5
```

## Como Rodar

Inicie o Ollama:

```bash
ollama serve
```

Inicie o backend:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Inicie o frontend:

```bash
cd frontend
npm run dev
```

Acesse:

```text
http://localhost:5173
```

## Fluxo de Uso

1. Faça upload de uma planilha `.xlsx`, `.xls` ou `.csv`.
2. Confira a visão geral e o tipo detectado automaticamente.
3. Use a aba **Visualizações** para navegar pelos painéis específicos.
4. Opcionalmente informe um contexto para a análise.
5. Clique em **Analisar com IA** para gerar insights via Ollama.
6. Exporte os dados ou o relatório quando necessário.

## Estrutura do Projeto

```text
ux_analysis_pipeline/
├── backend/
│   ├── main.py                 # API FastAPI
│   ├── data_processing.py      # Limpeza, classificação e dados para visualizações
│   └── requirements.txt        # Dependências Python do backend
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Layout principal e fluxo da aplicação
│   │   ├── api.js              # Cliente HTTP
│   │   ├── i18n.jsx            # Traduções PT/EN
│   │   ├── index.css           # Design system
│   │   └── components/         # Painéis, upload, cards e tabelas
│   ├── index.html
│   └── package.json
├── samples/                    # Exemplos de teste de usabilidade e perfil
├── ux_excel_analyzer.py        # Motor de análise com Ollama
├── README.md
└── .gitignore
```

## API Principal

- `GET /api/health`: verifica backend e conexão com Ollama.
- `POST /api/upload`: recebe planilha, limpa dados e detecta o tipo.
- `GET /api/visualizations`: retorna dados prontos para os painéis.
- `POST /api/analyze`: executa a análise com IA local.
- `GET /api/export/csv`: exporta a base carregada em CSV.
- `GET /api/export/excel`: exporta a base carregada em Excel.
- `GET /api/export/report`: exporta o relatório de IA em JSON.

## Amostras

A pasta `samples/` contém exemplos dos dois principais cenários suportados:

- Testes de usabilidade:
  - `Teste_Usabilidade_Analise_Logs.xlsx`
  - `Teste_Usabilidade_Deploy_Automatizado.xlsx`
  - `Teste_Usabilidade_Gestao_BancoDados.xlsx`
  - `Teste_Usabilidade_Gestao_Incidentes.xlsx`
  - `Teste_Usabilidade_Monitoramento_Cloud.xlsx`
- Mapeamentos de perfil:
  - `Mapeamento_Perfil_Analise_Logs.xlsx`
  - `Mapeamento_Perfil_Deploy_Automatizado.xlsx`
  - `Mapeamento_Perfil_Gestao_BancoDados.xlsx`
  - `Mapeamento_Perfil_Gestao_Incidentes.xlsx`
  - `Mapeamento_Perfil_Monitoramento_Cloud.xlsx`

Esses arquivos servem como referência para validar extração de tarefas, tempos, classificações, perfil da amostra, notas e temas recorrentes.

## Tecnologias

| Camada | Tecnologias |
| --- | --- |
| Frontend | React, Vite |
| Visualizações | Recharts |
| Ícones | Lucide React |
| Backend | FastAPI |
| Dados | Pandas, NumPy, OpenPyXL |
| IA local | Ollama, qwen2.5 |
| Validação | Pydantic |

## Licença

MIT
