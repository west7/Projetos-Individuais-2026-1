# Comandos do Projeto 4

Todos os comandos devem ser executados na pasta:

```bash
cd guilherme-westphall/projeto-4
```

## Ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Arquivo `.env` para Gemini:

```bash
GEMINI_API_KEY=sua_chave_aqui
```

## Ingestão

Coletar MRV e Pacaembu:

```bash
python -m src.cli ingest --company all
```

Coletar uma empresa:

```bash
python -m src.cli ingest --company mrv
python -m src.cli ingest --company pacaembu
```

Limitar downloads para demonstração:

```bash
python -m src.cli ingest --company all --limit 2
```

## Parsing

Extrair texto dos PDFs catalogados:

```bash
python -m src.cli parse-documents --company all
```

Limitar parsing:

```bash
python -m src.cli parse-documents --company all --limit 2
```

## Extração

Processar com mock:

```bash
python -m src.cli process --extractor mock --company all --limit 2
```

Atalho legado do mock:

```bash
python -m src.cli process-mock --company all --limit 2
```

Processar com Gemini:

```bash
python -m src.cli process --extractor gemini --company all --limit 2
```

## Listagens

Listar documentos:

```bash
python -m src.cli list-documents
```

Listar métricas:

```bash
python -m src.cli list-metrics
```

## SQLite

Abrir banco:

```bash
sqlite3 data/catalog.db
```

Métricas:

```sql
.headers on
.mode column

SELECT company, year, quarter, metric_name, value, unit, confidence, extractor_name
FROM metrics
ORDER BY company, metric_name, unit;
```

Documentos e status:

```sql
SELECT company, year, quarter, status, document_title
FROM documents
ORDER BY company, year DESC, quarter DESC;
```

Linhagem:

```sql
SELECT d.company, d.document_title, d.document_url, d.sha256, m.metric_name, m.value, m.unit
FROM metrics m
JOIN documents d ON d.id = m.document_id
ORDER BY d.company, m.metric_name;
```

Textos parseados:

```sql
SELECT d.company, d.document_title, t.page_count, length(t.text) AS text_chars, t.parsed_at
FROM document_texts t
JOIN documents d ON d.id = t.document_id
ORDER BY d.company;
```

Sair:

```sql
.quit
```

## Testes

```bash
pytest -q
```
