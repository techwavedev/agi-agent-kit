---
name: junta-leiloeiros
description: Coleta e consulta dados de leiloeiros oficiais de todas as 27 Juntas Comerciais do Brasil. Scraper multi-UF, banco SQLite, API FastAPI e exportacao CSV/JSON.
risk: safe
source: community
date_added: '2026-03-06'
author: renat
tags:
- scraping
- brazilian-data
- auctioneers
- api
tools:
- claude-code
- antigravity
- cursor
- gemini-cli
- codex-cli
---

# Skill: Leiloeiros das Juntas Comerciais do Brasil

## Overview

Coleta e consulta dados de leiloeiros oficiais de todas as 27 Juntas Comerciais do Brasil. Scraper multi-UF, banco SQLite, API FastAPI e exportacao CSV/JSON.

## When to Use This Skill

- When the user mentions "leiloeiro junta" or related topics
- When the user mentions "junta comercial leiloeiro" or related topics
- When the user mentions "scraper junta" or related topics
- When the user mentions "jucesp leiloeiro" or related topics
- When the user mentions "jucerja" or related topics
- When the user mentions "jucemg leiloeiro" or related topics

## Do Not Use This Skill When

- The task is unrelated to junta leiloeiros
- A simpler, more specific tool can handle the request
- The user needs general-purpose assistance without domain expertise

## How It Works

Coleta dados públicos de leiloeiros oficiais de todas as 27 Juntas Comerciais estaduais,
persiste em banco SQLite local e oferece API REST e exportação em múltiplos formatos.

## Localização

```
C:\Users\renat\skills\junta-leiloeiros\
├── scripts/
│   ├── scraper/
│   │   ├── base_scraper.py      ← classe abstrata
│   │   ├── states.py            ← registro dos 27 scrapers
│   │   ├── jucesp.py / jucerja.py / jucemg.py / jucec.py / jucis_df.py
│   │   └── generic_scraper.py   ← usado pelos 22 estados restantes
│   ├── db.py                    ← banco SQLite
│   ├── run_all.py               ← orquestrador de scraping
│   ├── serve_api.py             ← API FastAPI
│   ├── export.py                ← exportação
│   └── requirements.txt
├── references/
│   ├── juntas_urls.md           ← URLs e status de todas as 27 juntas
│   ├── schema.md                ← schema do banco
│   └── legal.md                 ← base legal
└── data/
    ├── leiloeiros.db            ← banco SQLite (criado no primeiro run)
    ├── scraping_log.json        ← log de cada coleta
    └── exports/                 ← arquivos exportados
```

## Instalação (Uma Vez)

```bash
pip install -r C:\Users\renat\skills\junta-leiloeiros\scripts\requirements.txt

## Para Sites Com Javascript:

playwright install chromium
```

## Coletar Dados

```bash

## Todos Os 27 Estados

python C:\Users\renat\skills\junta-leiloeiros\scripts\run_all.py

## Estados Específicos

python C:\Users\renat\skills\junta-leiloeiros\scripts\run_all.py --estado SP RJ MG

## Ver O Que Seria Coletado Sem Executar

python C:\Users\renat\skills\junta-leiloeiros\scripts\run_all.py --dry-run

## Controlar Paralelismo (Default: 5)

python C:\Users\renat\skills\junta-leiloeiros\scripts\run_all.py --concurrency 3
```

## Estatísticas Por Estado

python C:\Users\renat\skills\junta-leiloeiros\scripts\db.py

## Sql Direto

sqlite3 C:\Users\renat\skills\junta-leiloeiros\data\leiloeiros.db \
  "SELECT estado, COUNT(*) FROM leiloeiros GROUP BY estado"
```

## Servir Api Rest

```bash
python C:\Users\renat\skills\junta-leiloeiros\scripts\serve_api.py

## Docs Interativos: Http://Localhost:8000/Docs

```

**Endpoints:**
- `GET /leiloeiros?estado=SP&situacao=ATIVO&nome=silva&limit=100`
- `GET /leiloeiros/{estado}` — ex: `/leiloeiros/SP`
- `GET /busca?q=texto`
- `GET /stats`
- `GET /export/json`
- `GET /export/csv`

## Exportar Dados

```bash
python C:\Users\renat\skills\junta-leiloeiros\scripts\export.py --format csv
python C:\Users\renat\skills\junta-leiloeiros\scripts\export.py --format json
python C:\Users\renat\skills\junta-leiloeiros\scripts\export.py --format all
python C:\Users\renat\skills\junta-leiloeiros\scripts\export.py --format csv --estado SP
```

## Usar Em Código Python

```python
import sys
sys.path.insert(0, r"C:\Users\renat\skills\junta-leiloeiros\scripts")
from db import Database

db = Database()
db.init()

## Todos Os Leiloeiros Ativos De Sp

leiloeiros = db.get_all(estado="SP", situacao="ATIVO")

## Busca Por Nome

resultados = db.search("silva")

## Estatísticas

stats = db.get_stats()
```

## Adicionar Scraper Customizado

Se um estado precisar de lógica específica (ex: site usa JavaScript):

```python

## Scripts/Scraper/Meu_Estado.Py

from .base_scraper import AbstractJuntaScraper, Leiloeiro
from typing import List

class MeuEstadoScraper(AbstractJuntaScraper):
    estado = "XX"
    junta = "JUCEX"
    url = "https://www.jucex.xx.gov.br/leiloeiros"

    async def parse_leiloeiros(self) -> List[Leiloeiro]:
        soup = await self.fetch_page()
        if not soup:
            return []
        # lógica específica aqui
        return [self.make_leiloeiro(nome="...", matricula="...")]
```

Registrar em `scripts/scraper/states.py`:
```python
from .meu_estado import MeuEstadoScraper
SCRAPERS["XX"] = MeuEstadoScraper
```

## Referências

- URLs de todas as juntas: `references/juntas_urls.md`
- Schema do banco: `references/schema.md`
- Base legal da coleta: `references/legal.md`
- Log de coleta: `data/scraping_log.json`

## Best Practices

- Provide clear, specific context about your project and requirements
- Review all suggestions before applying them to production code
- Combine with other complementary skills for comprehensive analysis

## Common Pitfalls

- Using this skill for tasks outside its domain expertise
- Applying recommendations without understanding your specific context
- Not providing enough project context for accurate analysis

## Related Skills

- `leiloeiro-avaliacao` - Complementary skill for enhanced analysis
- `leiloeiro-edital` - Complementary skill for enhanced analysis
- `leiloeiro-ia` - Complementary skill for enhanced analysis
- `leiloeiro-juridico` - Complementary skill for enhanced analysis
- `leiloeiro-mercado` - Complementary skill for enhanced analysis

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Junta Leiloeiros"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags junta-leiloeiros backend
```

### Multi-Agent Collaboration

Share API contract changes with frontend agents so they update their client code, and with QA agents for test coverage.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented API endpoints — 5 new routes with OpenAPI spec and integration tests" \
  --project <project>
```

### Agent Team: Code Review

After implementation, dispatch `code_review_team` for two-stage review (spec compliance + code quality) before merging.

<!-- AGI-INTEGRATION-END -->
