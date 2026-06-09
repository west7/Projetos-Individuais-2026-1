# Projeto 4 - Pipeline UDA para PDFs de RI

Este projeto implementa um pipeline de UDA (Unstructured Data Analysis) para coletar, catalogar, parsear e extrair métricas de PDFs de Relações com Investidores de empresas do setor habitacional.

O foco da entrega é demonstrar um fluxo robusto e simples:

1. coleta de PDFs de MRV e Pacaembu;
2. idempotência por URL e hash SHA-256;
3. catálogo SQLite com linhagem;
4. parsing de texto dos PDFs;
5. contrato semântico com Pydantic;
6. extração mock e extração real com Google Gemini;
7. consultas das métricas extraídas via CLI e SQLite.

## Fontes monitoradas

- MRV: https://ri.mrv.com.br/informacoes-financeiras/central-de-resultados/
- Pacaembu: https://ri.pacaembu.com/

Observação: a MRV carrega parte dos documentos dinamicamente. Por isso, a implementação inclui uma URL-semente direta para a Prévia Operacional MRV 1T26. A Pacaembu funciona por scraping da página de RI.

## Arquitetura

O pipeline está dividido em módulos pequenos:

- `src/sources.py`: configuração das fontes MRV e Pacaembu.
- `src/scraper.py`: descobre links candidatos nas páginas de RI.
- `src/downloader.py`: baixa PDFs, valida assinatura `%PDF` e calcula SHA-256.
- `src/catalog.py`: cria e atualiza o catálogo SQLite.
- `src/pdf_parser.py`: extrai texto dos PDFs usando `pypdf`.
- `src/schemas.py`: define o contrato semântico Pydantic.
- `src/extractor.py`: implementa extrator mock e extrator Gemini.
- `src/process.py`: orquestra extração e persistência das métricas.
- `src/cli.py`: comandos de linha de comando.
- `prompts/extraction_prompt.md`: prompt usado pelo Gemini.

## Banco de dados

O banco local fica em:

```text
data/catalog.db
```

Ele não é versionado. As tabelas principais são:

- `documents`: catálogo e linhagem dos PDFs coletados.
- `document_texts`: texto extraído dos PDFs.
- `metrics`: métricas extraídas pelo mock ou Gemini.

Cada métrica fica associada ao `document_id`, preservando a origem do dado.

## Instalação

```bash
cd guilherme-westphall/projeto-4
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para usar Gemini, crie um arquivo `.env` na raiz do projeto:

```bash
GEMINI_API_KEY=sua_chave_aqui
```

O arquivo `.env` está no `.gitignore` e não deve ser versionado.

## Execução do pipeline

Fluxo completo com Gemini:

```bash
python -m src.cli ingest --company all --limit 2
python -m src.cli parse-documents --company all --limit 2
python -m src.cli process --extractor gemini --company all --limit 2
python -m src.cli list-metrics
```

Fluxo usando mock:

```bash
python -m src.cli ingest --company all --limit 2
python -m src.cli process --extractor mock --company all --limit 2
python -m src.cli list-metrics
```

O comando legado abaixo também foi mantido:

```bash
python -m src.cli process-mock --company all --limit 2
```

Veja todos os comandos em [COMMANDS.md](COMMANDS.md).

## Contrato semântico

O contrato Pydantic exige que cada resposta contenha:

- `company`
- `year`
- `quarter`
- `metrics`

Cada métrica deve conter:

- `metric_name`: atualmente `lancamentos` ou `vendas`;
- `value`: valor absoluto ou `null`;
- `unit`: unidade do valor;
- `confidence`: `high`, `medium`, `low` ou `mock`;
- `evidence`: trecho curto do documento usado como evidência.

O prompt instrui o LLM a:

- extrair apenas valores absolutos;
- ignorar percentuais de variação como valor principal;
- não inventar dados;
- retornar `null` quando o valor não estiver claro.

## Evidências

As evidências registradas estão no arquivo [evidences](evidences).

Resultado obtido com Gemini:

```text
Processamento concluido: 2 documentos, 6 metricas, 0 parseados sob demanda, 0 falharam.
```

Métricas persistidas:

```text
MRV | 1T26 | lancamentos | None R$ milhões | gemini-2.5-flash
MRV | 1T26 | vendas | None R$ milhões | gemini-2.5-flash
Pacaembu | 1T26 | lancamentos | 4279.0 unidades | gemini-2.5-flash
Pacaembu | 1T26 | lancamentos | 856.4 R$ milhões | gemini-2.5-flash
Pacaembu | 1T26 | vendas | 4302.0 unidades | gemini-2.5-flash
Pacaembu | 1T26 | vendas | 867.1 R$ milhões | gemini-2.5-flash
```

A Pacaembu retornou valores absolutos em unidades e em R$ milhões. A MRV foi processada, mas o Gemini retornou `null` para os valores absolutos buscados, com baixa confiança. Isso é aceitável para a demonstração do contrato semântico, porque o pipeline não inventou valores quando eles não estavam claros no texto parseado.

## Consultas SQLite

Abrir o banco:

```bash
sqlite3 data/catalog.db
```

Configurar saída:

```sql
.headers on
.mode column
```

Listar métricas:

```sql
SELECT company, year, quarter, metric_name, value, unit, confidence, extractor_name
FROM metrics
ORDER BY company, metric_name, unit;
```

Verificar status dos documentos:

```sql
SELECT company, year, quarter, status, document_title
FROM documents
ORDER BY company, year DESC, quarter DESC;
```

Verificar linhagem:

```sql
SELECT d.company, d.document_title, d.document_url, d.sha256, m.metric_name, m.value, m.unit
FROM metrics m
JOIN documents d ON d.id = m.document_id
ORDER BY d.company, m.metric_name;
```

Verificar textos parseados:

```sql
SELECT d.company, d.document_title, t.page_count, length(t.text) AS text_chars, t.parsed_at
FROM document_texts t
JOIN documents d ON d.id = t.document_id
ORDER BY d.company;
```

Sair do SQLite:

```sql
.quit
```

## Testes

```bash
pytest -q
```

Resultado atual:

```text
14 passed
```

## Limitações conhecidas

- A estratégia atual usa Full-Scan do texto extraído; chunking semântico ficaria como evolução.
- A MRV usa URL-semente porque a página de RI não expõe todos os PDFs no HTML estático.
- O pipeline não possui frontend.
- A API REST ainda não foi implementada; a consulta atual é feita por CLI e SQLite.
- O Gemini depende da chave `GEMINI_API_KEY` no `.env`.
