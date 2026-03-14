# 🚀 AGI Agent Kit

🌐 Português (BR) | _[English](./README.md)_

> **Pare de alucinar. Comece a executar.**

[![npm version](https://img.shields.io/npm/v/@techwavedev/agi-agent-kit.svg)](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)
[![npm downloads](https://img.shields.io/npm/dw/@techwavedev/agi-agent-kit.svg)](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Anthropic-purple)](https://claude.ai)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-Google-blue)](https://github.com/google-gemini/gemini-cli)
[![Codex CLI](https://img.shields.io/badge/Codex%20CLI-OpenAI-green)](https://github.com/openai/codex)
[![Cursor](https://img.shields.io/badge/Cursor-AI%20IDE-orange)](https://cursor.sh)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-VSCode-lightblue)](https://github.com/features/copilot)
[![OpenCode](https://img.shields.io/badge/OpenCode-CLI-gray)](https://github.com/opencode-ai/opencode)
[![Antigravity IDE](https://img.shields.io/badge/Antigravity-DeepMind-red)](https://github.com/techwavedev/agi-agent-kit)
[![AdaL CLI](https://img.shields.io/badge/AdaL%20CLI-SylphAI-pink)](https://sylph.ai/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-CLI-teal)](https://github.com/openclaw/openclaw)
[![Kiro](https://img.shields.io/badge/Kiro-AWS-yellow)](https://kiro.dev)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blueviolet)](https://modelcontextprotocol.io)
[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a-coffee-d13610?logo=buymeacoffee&logoColor=white)](https://www.buymeacoffee.com/eltonmachado)

**AGI Agent Kit** é o scaffolding de nível empresarial que transforma qualquer assistente de código com IA em uma **máquina de produção determinística**. Enquanto LLMs são probabilísticos (90% de precisão por etapa = 59% ao longo de 5 etapas), este framework os força através de uma **Arquitetura de 3 Camadas** — Intenção → Orquestração → Execução — onde a lógica de negócio vive em scripts testados, não em código alucinado.

## Por que isso existe

A maioria das configurações de IA para código te dá um prompt e torce pelo melhor. O AGI Agent Kit te oferece:

- 🧠 **Memória Híbrida** — Vetores Qdrant + palavras-chave BM25: similaridade semântica para conceitos, correspondência exata para códigos de erro e IDs (90-100% de economia de tokens)
- 🎯 **19 Agentes Especialistas** — Experts delimitados por domínio (Frontend, Backend, Segurança, Mobile, Game Dev...) com propriedade de arquivos forçada
- ⚡ **1.191 Skills Curadas** — 4 essenciais + 89 profissionais + 1.098 comunitárias em 16 categorias de domínio
- 🔒 **Portões de Verificação** — Nenhuma tarefa é concluída sem evidência. Enforcement de TDD. Revisão de código em duas etapas.
- 🌐 **10 Plataformas, Uma Configuração** — Escreva uma vez, execute no Claude Code, Gemini CLI, Codex CLI, Cursor, Copilot, OpenCode, AdaL CLI, Antigravity IDE, OpenClaw, Kiro
- 🔌 **Compatível com MCP** — Expõe memória + coordenação entre agentes como ferramentas MCP para Claude Desktop e qualquer cliente de interface de chat

```bash
npx @techwavedev/agi-agent-kit init
```

Se este projeto te ajuda, considere [apoiá-lo aqui](https://www.buymeacoffee.com/eltonmachado) ou simplesmente ⭐ o repositório.

---

## 🚀 Início Rápido

Monte um novo workspace de agente em segundos:

```bash
npx @techwavedev/agi-agent-kit init

# Ou instale globalmente em ~/.agent para compartilhar skills entre projetos
npx @techwavedev/agi-agent-kit init --global
```

Você será guiado por um assistente interativo:

1. **Verificação de instalação existente** — detecta uma instalação prévia e oferece Atualizar / Reinstalar / Cancelar
2. **Escopo da instalação** — local ao projeto (diretório atual) ou global (`~/.agent` compartilhado entre projetos)
3. **Backup inteligente** — verifica os arquivos em risco e cria um backup com timestamp antes de alterar qualquer coisa
4. **Seleção de pacote** — escolha as skills para instalar:
   - **core** — 4 skills essenciais (webcrawler, pdf-reader, qdrant-memory, documentation)
   - **medium** — Core + 89 skills profissionais em 16 categorias + estrutura `.agent/`
   - **full** — Tudo: Medium + 1.098 skills comunitárias (1.191 no total)
   - **custom** — Core + você escolhe domínios específicos (AI Agents, DevOps, Segurança, Frontend, etc.)
5. **Configuração de memória** — detecta Ollama/Docker/Qdrant; se ausente, pergunta se deseja instalar localmente ou usar uma URL personalizada (suporta Qdrant Cloud, servidores remotos)
6. **Agent Teams** — opt-in para execução multi-agente paralela (grava `.claude/settings.json`)
7. **Resumo** — mostra exatamente o que foi configurado e o que precisa de ação manual

Após a instalação, o assistente mostra seus próximos passos, incluindo:

```bash
# Inicializar o sistema de memória (verifica Qdrant + Ollama, corrige automaticamente)
python3 execution/session_boot.py --auto-fix

# Executar o assistente de configuração de plataforma (auto-configura sua plataforma de IA)
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .
```

---

## ✨ Funcionalidades Principais

| Funcionalidade                    | Descrição                                                                                     |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| **Execução Determinística**       | Separa lógica de negócio (scripts Python) do raciocínio da IA (Diretivas)                     |
| **Sistema Modular de Skills**     | 1.191 skills plug-and-play em 3 níveis, organizadas em 16 categorias de domínio                 |
| **Execução de Plano Estruturado** | Execução em lote ou orientada por subagentes com revisão em duas etapas (spec + qualidade)    |
| **Enforcement de TDD**            | Ciclo RED-GREEN-REFACTOR inquebrantável — sem código de produção sem teste falhando           |
| **Portões de Verificação**        | Evidência antes de afirmações — sem conclusão sem saída de verificação atualizada             |
| **Adaptativo à Plataforma**       | Auto-detecta Claude Code, Gemini CLI, Codex CLI, Cursor, Copilot, OpenCode, AdaL, Antigravity, Kiro |
| **Compatível com MCP**            | Memória + coordenação entre agentes expostas como ferramentas MCP (`execution/mcp_server.py`) para Claude Desktop e qualquer cliente MCP |
| **Orquestração Multi-Agente**     | Agent Teams, subagentes, Powers, ou personas sequenciais — adapta-se à plataforma             |
| **Memória Híbrida**               | Vetores Qdrant + palavras-chave BM25 com mesclagem de pontuação ponderada (95% de economia)   |
| **Workflows Auto-Reparáveis**     | Agentes leem logs de erro, corrigem scripts e atualizam diretivas automaticamente             |
| **Configuração em Um Comando**    | Detecção de plataforma + varredura de stack + auto-configuração em um único comando           |

---

## 🆚 Como Isso Se Compara ao Superpowers

O framework AGI adota todos os melhores padrões do [obra/superpowers](https://github.com/obra/superpowers) e os estende com capacidades que o Superpowers não possui:

| Capacidade                       | obra/superpowers |             Framework AGI             |
| -------------------------------- | :--------------: | :-----------------------------------: |
| Enforcement de TDD               |        ✅        |              ✅ Adaptado              |
| Execução de Plano + Revisão      |        ✅        | ✅ Adaptado + adaptativo à plataforma |
| Debugging Sistemático            |        ✅        |    ✅ Adaptado + agente `debugger`    |
| Portões de Verificação           |        ✅        |   ✅ Adaptado + 12 scripts de audit   |
| Revisão de Código em Duas Etapas |        ✅        |      ✅ Adaptado no orquestrador      |
| Orquestração Multi-Plataforma    | ❌ Apenas Claude |           ✅ 9 plataformas            |
| Memória Semântica (Qdrant)       |        ❌        |     ✅ 90-100% economia de tokens     |
| 19 Agentes Especialistas         |        ❌        |       ✅ Fronteiras de domínio        |
| Reforço de Fronteiras de Agente  |        ❌        |  ✅ Propriedade por tipo de arquivo   |
| Geração Dinâmica de Perguntas    |        ❌        |      ✅ Trade-offs + prioridades      |
| Protocolo Memory-First           |        ❌        |           ✅ Auto cache-hit           |
| Criador de Skills + Catálogo     |        ❌        |       ✅ 1.191 skills combináveis       |
| Assistente de Configuração       |        ❌        |     ✅ Configuração em um comando     |
| Symlinks Multi-Plataforma        | ❌ Apenas Claude |           ✅ 9 plataformas            |

---

## 🧪 Benchmark Real: Subagentes vs Agent Teams

O framework suporta dois modos de orquestração. Aqui estão **resultados reais de teste** de `execution/benchmark_modes.py` rodando em infraestrutura local (Qdrant + Ollama `nomic-embed-text`, zero chamadas de API na nuvem):

```text
MODO A: SUBAGENTES — Independentes, fire-and-forget
  📤 Explorar Padrões de Auth   → ✅ armazenado em cache + memória (127ms)
  📤 Performance de Query       → ❌ FALHOU (timeout — tolerante a falhas)
  📤 Varrer CVEs                → ✅ armazenado em cache + memória (14ms)
  Resumo: 2/3 concluídos, 1 falhou, 0 referências cruzadas

MODO B: AGENT TEAMS — Contexto compartilhado, coordenado
  👤 Especialista Backend       → ✅ armazenado em memória compartilhada (14ms)
  👤 Especialista Banco de Dados → ✅ armazenado em memória compartilhada (13ms)
  👤 Especialista Frontend      → 🔗 Leu primeiro a saída do Backend + Banco de Dados
     ✅ Obteve contexto de team-backend: "Contrato de API: POST /api/messages..."
     ✅ Obteve contexto de team-database: "Schema: users(id UUID PK, name..."
     → ✅ armazenado em memória compartilhada (14ms)
  Resumo: 3/3 concluídos, 0 falhas, 2 referências cruzadas
```

**2ª execução (cache aquecido):** Todas as consultas atingem o cache com **score 1.000**, reduzindo o tempo total de 314ms → 76ms (Subagentes) e 292ms → 130ms (Agent Teams).

| Métrica                | Subagentes                           | Agent Teams                              |
| ---------------------- | ------------------------------------ | ---------------------------------------- |
| Modelo de execução     | Fire-and-forget (isolado)            | Contexto compartilhado (coordenado)      |
| Tarefas concluídas     | 2/3 (tolerante a falhas)             | 3/3                                      |
| Referências cruzadas   | 0 (não suportado)                    | 2 (pares leem o trabalho uns dos outros) |
| Compartilhamento       | ❌ Cada agente isolado               | ✅ Peer-to-peer via Qdrant               |
| Revisão em duas etapas | ❌                                   | ✅ Spec + Qualidade                      |
| Cache hits (2ª exec)   | 5/5                                  | 5/5                                      |
| Provedor de embedding  | Ollama local (nomic-embed-text 137M) | Ollama local (nomic-embed-text 137M)     |

**Experimente você mesmo:**

```bash
# 1. Iniciar infraestrutura
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
ollama serve & ollama pull nomic-embed-text

# 2. Inicializar sistema de memória
python3 execution/session_boot.py --auto-fix
# ✅ Sistema de memória pronto — 5 memórias, 1 resposta em cache

# 3. Rodar o benchmark completo (ambos os modos)
python3 execution/benchmark_modes.py --verbose

# 4. Ou testar operações individuais:

# Armazenar uma decisão (embedding gerado localmente via Ollama)
python3 execution/memory_manager.py store \
  --content "Escolhemos PostgreSQL para dados relacionais" \
  --type decision --project myapp
# → {"status": "stored", "point_id": "...", "token_count": 5}

# Auto-consulta: verifica cache primeiro, depois recupera contexto
python3 execution/memory_manager.py auto \
  --query "qual banco de dados escolhemos?"
# → {"source": "memory", "cache_hit": false, "context_chunks": [...]}

# Armazenar uma resposta de LLM em cache para reutilização futura
python3 execution/memory_manager.py cache-store \
  --query "como configurar auth?" \
  --response "Use JWT com expiração de 24h, refresh tokens em cookies httpOnly"

# Re-consulta → cache hit instantâneo (score 1.000, zero recomputação)
python3 execution/memory_manager.py auto \
  --query "como configurar auth?"
# → {"source": "cache", "cache_hit": true, "tokens_saved_estimate": 12}
```

## 🌐 Suporte a Plataformas

O framework detecta automaticamente seu ambiente de codificação com IA e ativa as melhores funcionalidades disponíveis.

Skills são instaladas no diretório canônico `skills/` e vinculadas via symlink ao caminho esperado de cada plataforma:

| Plataforma          | Caminho das Skills | Arquivo de Instrução | Estratégia de Orquestração           |
| ------------------- | ------------------ | -------------------- | ------------------------------------ |
| **Claude Code**     | `.claude/skills/`  | `CLAUDE.md`          | Agent Teams (paralelo) ou Subagentes |
| **Gemini CLI**      | `.gemini/skills/`  | `GEMINI.md`          | Personas sequenciais via `@agent`    |
| **Codex CLI**       | `.codex/skills/`   | `AGENTS.md`          | Sequencial via prompts               |
| **Antigravity IDE** | `.agent/skills/`   | `AGENTS.md`          | Orquestração agêntica completa       |
| **Cursor**          | `.cursor/skills/`  | `AGENTS.md`          | Baseado em chat via `@skill`         |
| **GitHub Copilot**  | N/A (colar)        | `COPILOT.md`         | Colar manualmente no contexto        |
| **OpenCode**        | `.agent/skills/`   | `OPENCODE.md`        | Personas sequenciais via `@agent`    |
| **AdaL CLI**        | `.adal/skills/`    | `AGENTS.md`          | Carregamento automático sob demanda  |

Execute `/setup` para auto-detectar e configurar sua plataforma, ou use o script de configuração diretamente:

```bash
# Interativo (uma pergunta Y/n)
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .

# Auto-aplicar tudo
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --auto

# Pré-visualizar sem alterações
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --dry-run
```

---

## 📦 O Que Você Recebe

```text
seu-projeto/
├── AGENTS.md              # Arquivo de instrução principal
├── GEMINI.md → AGENTS.md  # Symlinks de plataforma
├── CLAUDE.md → AGENTS.md
├── OPENCODE.md → AGENTS.md
├── COPILOT.md → AGENTS.md
├── skills/                # Até 1.191 skills (depende do pacote)
│   ├── webcrawler/        # Coleta de documentação
│   ├── qdrant-memory/     # Cache semântico & memória
│   └── ...                # Mais 877 skills no pacote completo
├── .claude/skills → skills/   # Symlinks específicos da plataforma
├── .gemini/skills → skills/
├── .codex/skills → skills/
├── .cursor/skills → skills/
├── .adal/skills → skills/
├── directives/            # SOPs em Markdown
├── execution/             # Scripts Python determinísticos
│   ├── session_boot.py    # Inicialização de sessão (verificação Qdrant + Ollama)
│   └── memory_manager.py  # Operações de armazenar/recuperar/cache
├── skill-creator/         # Ferramentas para criar novas skills
└── .agent/                # (medium/full) Agentes, workflows, regras
    └── workflows/         # /setup, /deploy, /test, /debug, etc.
```

---

## 📖 Arquitetura

O sistema opera em três camadas:

```text
┌─────────────────────────────────────────────────────────┐
│  Camada 1: DIRETIVAS (Intenção)                         │
│  └─ SOPs escritos em Markdown (directives/)             │
├─────────────────────────────────────────────────────────┤
│  Camada 2: ORQUESTRAÇÃO (Agente)                        │
│  └─ LLM lê a diretiva, decide qual ferramenta chamar    │
│  └─ Adaptativo à plataforma: Teams, Subagentes, Personas│
├─────────────────────────────────────────────────────────┤
│  Camada 3: EXECUÇÃO (Código)                            │
│  └─ Scripts Python puros (execution/) fazem o trabalho  │
└─────────────────────────────────────────────────────────┘
```

**Por quê?** LLMs são probabilísticos. 90% de precisão por etapa = 59% de sucesso ao longo de 5 etapas. Ao transferir a complexidade para scripts determinísticos, alcançamos execução confiável.

---

## 🧠 Memória Híbrida (BM25 + Vetorial)

Recuperação com motor duplo: similaridade vetorial Qdrant para conceitos semânticos + BM25 SQLite FTS5 para correspondência exata de palavras-chave. Mescla resultados automaticamente com pesos configuráveis.

| Cenário                   | Sem Memória  | Com Memória | Economia |
| ------------------------- | ------------ | ----------- | -------- |
| Pergunta repetida         | ~2000 tokens | 0 tokens    | **100%** |
| Arquitetura similar       | ~5000 tokens | ~500 tokens | **90%**  |
| Resolução de erro passado | ~3000 tokens | ~300 tokens | **90%**  |
| Busca exata de ID/código  | ~3000 tokens | ~200 tokens | **93%**  |

**Configuração** (requer [Qdrant](https://qdrant.tech/) + [Ollama](https://ollama.com/)):

```bash
# Iniciar Qdrant
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# Iniciar Ollama + baixar modelo de embedding
ollama serve &
ollama pull nomic-embed-text

# Inicializar sistema de memória (cria coleções automaticamente)
python3 execution/session_boot.py --auto-fix
```

Os agentes executam automaticamente `session_boot.py` no início da sessão (primeira instrução no `AGENTS.md`). Operações de memória:

```bash
# Auto-consulta (verificar cache + recuperar contexto)
python3 execution/memory_manager.py auto --query "resumo da sua tarefa"

# Armazenar uma decisão (auto-indexado no BM25)
python3 execution/memory_manager.py store --content "o que foi decidido" --type decision

# Verificação de saúde (inclui status do índice BM25)
python3 execution/memory_manager.py health

# Reconstruir índice BM25 a partir dos dados existentes no Qdrant
python3 execution/memory_manager.py bm25-sync
```

**Modos de busca híbrida** (via `hybrid_search.py`):

```bash
# Híbrido verdadeiro (padrão): vetorial + BM25 mesclados
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "erro ImagePullBackOff" --mode hybrid

# Apenas vetorial (semântico puro)
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "arquitetura de banco de dados" --mode vector

# Apenas palavras-chave (correspondência exata BM25)
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "sg-018f20ea63e82eeb5" --mode keyword
```

---

## ⚡ Pré-requisitos

O comando `npx init` cria automaticamente um `.venv` e instala todas as dependências. Basta ativá-lo:

```bash
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

Se precisar reinstalar ou atualizar as dependências:

```bash
.venv/bin/pip install -r requirements.txt
```

---

## 🔧 Comandos

### Inicializar um novo projeto

```bash
npx @techwavedev/agi-agent-kit init --pack=full
# Para instalar globalmente em vez de por projeto:
npx @techwavedev/agi-agent-kit init --pack=full --global
```

### Auto-detectar plataforma e configurar ambiente

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .
```

### Atualizar para a versão mais recente

```bash
npx @techwavedev/agi-agent-kit@latest init --pack=full
# ou use a skill integrada:
python3 skills/self-update/scripts/update_kit.py
```

### Inicializar sistema de memória

```bash
python3 execution/session_boot.py --auto-fix
```

### Verificação de saúde do sistema

```bash
python3 execution/system_checkup.py --verbose
```

### Criar uma nova skill

```bash
python3 skill-creator/scripts/init_skill.py my-skill --path skills/
```

### Atualizar catálogo de skills

```bash
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

## 🎯 Referência de Ativação

Use estas palavras-chave, comandos e frases para acionar funcionalidades específicas:

### Comandos Slash (Workflows)

| Comando         | O Que Faz                                             |
| --------------- | ----------------------------------------------------- |
| `/setup`        | Auto-detecta a plataforma e configura o ambiente      |
| `/setup-memory` | Inicializa o sistema de memória Qdrant + Ollama       |
| `/create`       | Inicia diálogo interativo de criação de app           |
| `/plan`         | Cria um plano de projeto estruturado (sem código)     |
| `/enhance`      | Adiciona ou atualiza funcionalidades em app existente |
| `/debug`        | Ativa modo de debugging sistemático                   |
| `/test`         | Gera e executa testes                                 |
| `/deploy`       | Verificações pré-deploy + implantação                 |
| `/orchestrate`  | Coordenação multi-agente para tarefas complexas       |
| `/brainstorm`   | Brainstorming estruturado com múltiplas opções        |
| `/preview`      | Iniciar/parar servidor de desenvolvimento local       |
| `/status`       | Mostrar progresso do projeto e painel de status       |
| `/update`       | Atualizar AGI Agent Kit para a versão mais recente    |
| `/checkup`      | Verificar agentes, workflows, skills e arquivos core  |

### Menções de Agente (`@agent`)

| Menção                    | Especialista                  | Quando Usar                                  |
| ------------------------- | ----------------------------- | -------------------------------------------- |
| `@orchestrator`           | Coordenador multi-agente      | Tarefas complexas multi-domínio              |
| `@project-planner`        | Especialista em planejamento  | Roadmaps, divisão de tarefas, fases          |
| `@frontend-specialist`    | Arquiteto de UI/UX            | Interfaces web, React, Next.js               |
| `@backend-specialist`     | Engenheiro de API/BD          | Server-side, bancos de dados, APIs           |
| `@mobile-developer`       | Especialista mobile           | iOS, Android, React Native, Flutter          |
| `@security-auditor`       | Especialista em segurança     | Varredura de vulnerabilidades, auditorias    |
| `@debugger`               | Especialista em debug         | Investigação de bugs complexos               |
| `@game-developer`         | Especialista em jogos         | Jogos 2D/3D, multiplayer, VR/AR              |
| `@devops-engineer`        | Especialista DevOps           | CI/CD, containers, infraestrutura cloud      |
| `@database-architect`     | Especialista em BD            | Design de schema, migrações, otimização      |
| `@documentation-writer`   | Especialista em docs          | Documentação técnica, APIs, READMEs          |
| `@test-engineer`          | Especialista em testes        | Estratégia de teste, automação, cobertura    |
| `@qa-automation-engineer` | Especialista em QA            | Testes E2E, regressão, quality gates         |
| `@performance-optimizer`  | Especialista em performance   | Profiling, gargalos, otimização              |
| `@seo-specialist`         | Especialista em SEO           | Otimização de busca, meta tags, rankings     |
| `@penetration-tester`     | Especialista em pen testing   | Exercícios red team, verificação de exploits |
| `@product-manager`        | Especialista em produto       | Requisitos, user stories, priorização        |
| `@code-archaeologist`     | Especialista em código legado | Entendimento de codebases antigos, migrações |
| `@explorer-agent`         | Especialista em descoberta    | Exploração de codebase, mapeamento de deps   |

### Palavras-Chave de Ativação de Skills (Linguagem Natural)

| Categoria             | Palavras / Frases de Ativação                                          | Skill Ativada                         |
| --------------------- | ---------------------------------------------------------------------- | ------------------------------------- |
| **Memória**           | "don't use cache", "no cache", "skip memory", "fresh"                  | Memory opt-out                        |
| **Pesquisa**          | "research my docs", "check my notebooks", "deep search", "@notebooklm" | `notebooklm-rag`                      |
| **Documentação**      | "update docs", "regenerate catalog", "sync documentation"              | `documentation`                       |
| **Qualidade**         | "lint", "format", "check", "validate", "static analysis"               | `lint-and-validate`                   |
| **Testes**            | "write tests", "run tests", "TDD", "test coverage"                     | `testing-patterns` / `tdd-workflow`   |
| **TDD**               | "test first", "red green refactor", "failing test"                     | `test-driven-development`             |
| **Execução de Plano** | "execute plan", "run the plan", "batch execution"                      | `executing-plans`                     |
| **Verificação**       | "verify", "prove it works", "evidence", "show me the output"           | `verification-before-completion`      |
| **Debugging**         | "debug", "root cause", "investigate", "why is this failing"            | `systematic-debugging`                |
| **Arquitetura**       | "design system", "architecture decision", "ADR", "trade-off"           | `architecture`                        |
| **Segurança**         | "security scan", "vulnerability", "audit", "OWASP"                     | `red-team-tactics`                    |
| **Performance**       | "lighthouse", "bundle size", "core web vitals", "profiling"            | `performance-profiling`               |
| **Design**            | "design UI", "color scheme", "typography", "layout"                    | `frontend-design`                     |
| **Deploy**            | "deploy", "rollback", "release", "CI/CD"                               | `deployment-procedures`               |
| **API**               | "REST API", "GraphQL", "tRPC", "API design"                            | `api-patterns`                        |
| **Banco de Dados**    | "schema design", "migration", "query optimization"                     | `database-design`                     |
| **Planejamento**      | "plan this", "break down", "task list", "requirements"                 | `plan-writing`                        |
| **Brainstorming**     | "explore options", "what are the approaches", "pros and cons"          | `brainstorming`                       |
| **Code Review**       | "review this", "code quality", "best practices"                        | `code-review-checklist`               |
| **i18n**              | "translate", "localization", "RTL", "locale"                           | `i18n-localization`                   |
| **AWS**               | "terraform", "EKS", "Lambda", "S3", "CloudFront"                       | `aws-skills` / `terraform-skill`      |
| **Infraestrutura**    | "service mesh", "Kubernetes", "Helm"                                   | `docker-expert` / `server-management` |

### Comandos do Sistema de Memória

| O Que Você Quer                   | Comando / Frase                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------- |
| **Inicializar memória**           | `python3 execution/session_boot.py --auto-fix`                                   |
| **Verificar antes de uma tarefa** | `python3 execution/memory_manager.py auto --query "..."`                         |
| **Armazenar uma decisão**         | `python3 execution/memory_manager.py store --content "..." --type decision`      |
| **Armazenar resposta em cache**   | `python3 execution/memory_manager.py cache-store --query "..." --response "..."` |
| **Verificação de saúde**          | `python3 execution/memory_manager.py health`                                     |
| **Pular cache para esta tarefa**  | Diga "fresh", "no cache" ou "skip memory" no seu prompt                          |

---

## 📚 Documentação

- **[AGENTS.md](./AGENTS.md)** — Arquitetura completa e princípios operacionais
- **[skills/SKILLS_CATALOG.md](./templates/skills/SKILLS_CATALOG.md)** — Catálogo de skills
- **[CHANGELOG.md](./CHANGELOG.md)** — Histórico de versões
- **[THIRD-PARTY-LICENSES.md](./THIRD-PARTY-LICENSES.md)** — Atribuições de terceiros

---

## 🤝 Skills da Comunidade & Créditos

O nível **Full** inclui 774 skills comunitárias adaptadas do projeto [Antigravity Awesome Skills](https://github.com/sickn33/antigravity-awesome-skills) (v5.4.0) por [@sickn33](https://github.com/sickn33), distribuídas sob a Licença MIT.

Esta coleção agrega skills de mais de 50 contribuidores e organizações open-source, incluindo Anthropic, Microsoft, Vercel Labs, Supabase, Trail of Bits, Expo, Sentry, Neon, fal.ai e muitos mais. Para o livro completo de atribuições, consulte [SOURCES.md](https://github.com/sickn33/antigravity-awesome-skills/blob/main/docs/SOURCES.md).

Cada skill comunitária foi adaptada para o framework AGI com:

- **Integração com Memória Qdrant** — Cache semântico e recuperação de contexto
- **Colaboração em Agent Teams** — Invocação orquestrada e memória compartilhada
- **Suporte a LLM Local** — Embeddings baseados em Ollama para operação local-first

Se essas skills comunitárias te ajudam, considere [dar uma estrela no repositório original](https://github.com/sickn33/antigravity-awesome-skills) ou [apoiar o autor](https://buymeacoffee.com/sickn33).

---

## 🗺️ Roadmap

| Funcionalidade                         | Status       | Descrição                                                                                                                                                                                                                                                           |
| -------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Memória Federada de Agentes**        | 🔬 Design    | Compartilhamento de conhecimento entre agentes via coleções Qdrant com escopo de projeto. Agentes no mesmo projeto leem decisões, erros e padrões uns dos outros — construindo inteligência coletiva entre sessões e plataformas.                                   |
| **Memória Autenticada por Blockchain** | 🔬 Design    | Camada de confiança criptográfica para memória compartilhada usando blockchains empresariais (Hyperledger Fabric, MultiChain ou Quorum) — auto-hospedado, sem taxas, sem criptomoeda. Escritas de agentes são assinadas, hashes de conteúdo são ancorados on-chain. |
| **Streaming de Agentes Event-Driven**  | 🔬 Design    | Comunicação em tempo real entre agentes via Kafka/Flink. Agentes publicam decisões e observações em tópicos, habilitando workflows reativos — ex: agente de segurança aciona remediação quando o agente de varredura publica achados.                               |
| **Motor de Workflows**                 | 📋 Planejado | Execução de playbooks `data/workflows.json` como sequências multi-skill guiadas com rastreamento de progresso e lógica de ramificação.                                                                                                                              |

---

## 🛡️ Segurança

Este pacote inclui um scanner de segurança pré-publicação que verifica termos privados antes de publicar. Todos os templates são sanitizados para uso público.

---

## ☕ Apoio

Se o AGI Agent Kit te ajuda a construir workflows melhores com IA, considere apoiar o projeto:

- ⭐ [Dê uma estrela no GitHub](https://github.com/techwavedev/agi-agent-kit)
- ☕ [Me pague um café](https://www.buymeacoffee.com/eltonmachado)

---

## 📄 Licença

Apache-2.0 © [Elton Machado@TechWaveDev](https://github.com/techwavedev)

Skills comunitárias no nível Full são licenciadas sob a Licença MIT. Consulte [THIRD-PARTY-LICENSES.md](./THIRD-PARTY-LICENSES.md) para detalhes.
