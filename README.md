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
- Uso do Ollama local com o modelo `qwen3:4b`.
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
Ollama local - qwen3:4b
```

## Pré-requisitos

- Python 3.9+
- Node.js 18+
- Ollama instalado e rodando localmente
- Modelo `qwen3:4b` disponível no Ollama

## Instalação

Faça estes passos apenas na primeira vez que for preparar o projeto.

1. Entre na pasta do projeto:

```bash
cd UX-Analysis-pipeline
```

2. Crie o ambiente virtual do Python:

```bash
python -m venv .venv
```

3. Ative o ambiente virtual:

```bash
.venv\Scripts\activate
```

Se o comando deu certo, o terminal deve mostrar `(.venv)` no começo da linha.

4. Instale as dependências do backend:

```bash
pip install -r backend/requirements.txt
```

5. Instale as dependências do frontend:

```bash
cd frontend
npm install
cd ..
```

6. Baixe o modelo local usado pela IA:

```bash
ollama pull qwen3:4b
```

## Como Rodar

Para usar o app, deixe 3 terminais abertos ao mesmo tempo.

### Terminal 1: Ollama

Inicie o servidor local do Ollama:

```bash
ollama serve
```

Deixe esse terminal aberto. Se aparecer uma mensagem dizendo que a porta já está em uso, provavelmente o Ollama já está rodando.

### Terminal 2: Backend

Na raiz do projeto, ative o ambiente virtual:

```bash
.venv\Scripts\activate
```

Depois inicie a API:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

O backend deve ficar disponível em:

```text
http://localhost:8000
```

Para testar rapidamente:

```text
http://localhost:8000/api/health
```

### Terminal 3: Frontend

Entre na pasta do frontend:

```bash
cd frontend
```

Inicie a interface:

```bash
npm run dev
```

Acesse o app no navegador:

```text
http://localhost:5173
```

## Rodar de Novo Depois

Depois que a instalação já foi feita uma vez, o fluxo diário é só:

1. Abrir o Ollama com `ollama serve`.
2. Abrir o backend com `.venv\Scripts\activate` e `python -m uvicorn backend.main:app --reload --port 8000`.
3. Abrir o frontend com `cd frontend` e `npm run dev`.
4. Entrar em `http://localhost:5173`.

## Problemas Comuns

- **`ollama` não é reconhecido**: instale o Ollama e abra um novo terminal.
- **Modelo não encontrado**: rode `ollama pull qwen3:4b`.
- **`python` não é reconhecido**: instale Python 3.9+ e marque a opção de adicionar ao PATH.
- **`npm` não é reconhecido**: instale Node.js 18+ e abra um novo terminal.
- **Frontend abre, mas não carrega dados**: confirme se o backend está rodando na porta `8000`.

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

- `Teste_Usabilidade_*.xlsx`
- `Mapeamento_Perfil_*.xlsx`

Esses arquivos servem como referência para validar extração de tarefas, tempos, classificações, perfil da amostra, notas e temas recorrentes.

## Tecnologias

| Camada | Tecnologias |
| --- | --- |
| Frontend | React, Vite |
| Visualizações | Recharts |
| Ícones | Lucide React |
| Backend | FastAPI |
| Dados | Pandas, NumPy, OpenPyXL |
| IA local | Ollama, qwen3:4b |
| Validação | Pydantic |

## Licença

MIT
