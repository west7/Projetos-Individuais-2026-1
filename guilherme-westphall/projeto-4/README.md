# Projeto 4 - Etapa 1: Coleta e Ingestao de PDFs

Primeira etapa do pipeline de UDA para o setor habitacional. Esta versao coleta PDFs das areas de RI da MRV e da Pacaembu, evita duplicidade por hash SHA-256 e registra a linhagem dos documentos em SQLite.

## Fontes monitoradas

- MRV: https://ri.mrv.com.br/informacoes-financeiras/central-de-resultados/
- Pacaembu: https://ri.pacaembu.com/

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.cli ingest --company all
python -m src.cli process-mock --company all
python -m src.cli list-documents
python -m src.cli list-metrics
```

Tambem e possivel processar uma empresa especifica:

```bash
python -m src.cli ingest --company mrv
python -m src.cli ingest --company pacaembu
```

Para demonstracoes rapidas, limite os downloads:

```bash
python -m src.cli ingest --company pacaembu --limit 2
```

## O que esta etapa faz

1. Acessa as paginas de RI configuradas.
2. Procura links candidatos de documentos financeiros.
3. Prioriza PDFs com textos como `Previa Operacional` e `Release de Resultados`.
4. Usa URLs-semente quando o site carrega os documentos dinamicamente, como no caso da MRV.
5. Baixa arquivos PDF.
6. Valida se o conteudo parece um PDF.
7. Calcula SHA-256.
8. Registra no catalogo SQLite com URL, empresa, trimestre, ano e caminho local.
9. Ignora documentos ja processados.

## Mock de LLM

Antes de integrar uma API real de LLM, o comando abaixo simula a extracao de metricas e grava os resultados no catalogo:

```bash
python -m src.cli process-mock --company all
python -m src.cli list-metrics
```

O mock gera metricas deterministicas para `lancamentos` e `vendas`. Os valores nao devem ser usados como resultado real; eles servem para validar o contrato, a persistencia e o fluxo de processamento.

## Catalogo de dados

O banco fica em `data/catalog.db` e possui a tabela `documents` com:

- empresa;
- URL da pagina fonte;
- URL do documento;
- titulo do documento;
- ano e trimestre inferidos;
- hash SHA-256;
- caminho local;
- status;
- datas de descoberta e download.

A tabela `metrics` armazena:

- documento de origem;
- empresa, ano e trimestre;
- nome da metrica;
- valor;
- unidade;
- confianca;
- extrator usado;
- data de extracao.

## Limitacoes

- Esta etapa ainda nao faz extracao semantica com LLM.
- A inferencia de ano/trimestre depende de padroes como `1T26`, `3T25`, `4T2025` no texto ou URL.
- Caso o site mude para carregamento totalmente dinamico, pode ser necessario trocar o coletor por Playwright.
