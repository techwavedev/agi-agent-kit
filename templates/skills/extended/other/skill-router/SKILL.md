---
name: skill-router
description: "Use when the user is unsure which skill to use or where to start. Interviews the user with targeted questions and recommends the best skill(s) from the installed library for their goal."
risk: safe
source: self
---

# Skill Router

## When to Use

Use this skill when:
- The user says "I don't know where to start" or "which skill should I use"
- The user has a vague goal without a clear method
- The user asks "what should I use for..." or "I'm not sure how to approach this"
- The user is new to the skill library and needs guidance

## Goal

Help users who are unsure of what they want to do or which skill to use.
Interview them with a short structured conversation, then recommend the most
relevant skill(s) from the installed library — with a clear explanation of
why each skill fits and exactly how to invoke it.

---

## Instructions

### Step 1 — Acknowledge and open the interview

Respond warmly and tell the user you'll ask a few quick questions to find
the right skill for them. Do NOT suggest any skills yet.

Example opener:
> "No problem — let me ask you a few quick questions so I can point you to
> exactly the right skill."

---

### Step 2 — Ask the Funnel Questions (one at a time, in order)

Ask only what you need. If an earlier answer makes a later question
irrelevant, skip it.

**Q1 — What is the broad area of the task?**
Present these as numbered options:
1. Building / coding something (app, feature, component, script)
2. Fixing or debugging something that's broken
3. Security, pentesting, or vulnerability assessment
4. AI agents, LLMs, or automation pipelines
5. Marketing, SEO, content, or growth
6. DevOps, infrastructure, deployment, or git
7. Design, UI/UX, or creative output
8. Planning, strategy, or documentation
9. Something else (ask them to describe it)

**Q2 — How specific is the task?**
1. I have a clear spec / I know exactly what I want built
2. I have a rough idea but need help shaping it
3. I'm totally starting from scratch with no clear direction

**Q3 — What tech stack or domain is involved?** (only ask if relevant)
Examples: React / Next.js, Node.js, Python, AWS, Stripe, AI/LLM, no-code, etc.
If they say "not sure" or "any", that's fine — move on.

**Q4 — Do you want to work autonomously (agent does everything) or
collaboratively (you stay in the loop)?**
1. Fully autonomous — just go
2. Collaborative — I want to review/approve steps
3. Not sure yet

---

### Step 3 — Recommend skills

Based on their answers, recommend **1 primary skill** and up to **2 secondary
skills**. Structure your recommendation exactly like this:

**✅ Primary Skill: `@skill-name`**
*Why:* [1–2 sentences explaining why this is the best fit for what they described]
*Invoke it like this:*
```
@skill-name [paste their goal here]
```

**🔁 Also consider:**
- `@skill-name-2` — [one sentence on when to layer this in]
- `@skill-name-3` — [one sentence on when to layer this in]

---

### Step 4 — Offer a ready-made prompt

After the recommendation, offer to write them a ready-to-use prompt they
can paste directly into Antigravity. Ask:

> "Want me to write the full prompt for you so you can just paste it in?"

If yes, compose a complete, specific prompt using the recommended skill and
everything you learned about their goal from the interview.

---

## Example Interaction

```
User: @skill-router I want to build something but I'm not sure where to start

Agent: No problem — let me ask a few quick questions.
       What is the broad area?
       (1) Building  (2) Debugging  (3) Security  (4) AI/LLM
       (5) Marketing  (6) DevOps  (7) Design  (8) Planning

User: 1 - building something

Agent: How specific is the task?
       (1) Clear spec  (2) Rough idea  (3) Starting from scratch

User: 2 - rough idea

Agent: What tech stack? (React, Node, Python, etc. — or "not sure")

User: Next.js

Agent: ✅ Primary Skill: @brainstorming
       Why: You have a rough idea that needs shaping before building.
       Brainstorming asks structured questions and produces a clear spec.

       @brainstorming help me design a [your app idea] using Next.js

       🔁 Also consider:
       - @plan-writing — once brainstorming produces a spec, break it into tasks
       - @senior-fullstack — when you are ready to start building

       Want me to write the full prompt for you?
```

---

## Skill Routing Reference

### Building a full product or app from scratch
- Primary: `@app-builder`
- If they want to plan first: `@brainstorming` → `@plan-writing` → `@app-builder`
- If they want it fully autonomous: `@loki-mode`

### Building a specific frontend feature / UI
- Primary: `@senior-fullstack` or `@frontend-design`
- Stack-specific: `@react-patterns`, `@nextjs-best-practices`, `@tailwind-patterns`
- If they want a full design system: `@ui-ux-pro-max` + `@core-components`

### Building a backend API or service
- Primary: `@backend-dev-guidelines`
- Stack-specific: `@nodejs-best-practices`, `@python-patterns`, `@nestjs-expert`
- API design: `@api-patterns`
- Database: `@database-design` + `@prisma-expert`

### Debugging something broken
- Primary: `@systematic-debugging`
- If tests are failing: `@test-fixing`
- If it's a code quality issue: `@clean-code`

### Writing tests / TDD
- Primary: `@tdd`
- For Playwright/browser tests: `@playwright-skill`
- For Jest patterns: `@testing-patterns`

### Integrating a third-party service
- Payments: `@stripe-integration`
- Auth: `@clerk-auth` or `@nextjs-supabase-auth`
- Database: `@neon-postgres` or `@firebase`
- Messaging: `@twilio-communications`
- Bots: `@slack-bot-builder`, `@discord-bot-architect`, `@telegram-bot-builder`
- File storage: `@file-uploads`
- Analytics: `@analytics-tracking`

### AI / LLM / agents
- Architecture: `@ai-agents-architect`
- RAG pipelines: `@rag-engineer`
- Prompts: `@prompt-engineer`
- Multi-agent: `@langgraph` or `@crewai`
- Observability: `@langfuse`
- Voice: `@voice-agents`

### Security / pentesting
- Start here: `@ethical-hacking-methodology` + `@pentest-checklist`
- Web app testing: `@burp-suite-testing`, `@sql-injection-testing`, `@xss-html-injection`
- Network/infra: `@aws-penetration-testing`, `@linux-privilege-escalation`
- Reference: `@top-web-vulnerabilities`

### DevOps / infrastructure / deployment
- Docker: `@docker-expert`
- Cloud: `@aws-serverless`, `@gcp-cloud-run`, `@vercel-deployment`
- Git workflow: `@git-pushing`, `@using-git-worktrees`, `@github-workflow-automation`
- Scripting: `@linux-shell-scripting`

### Marketing / growth / SEO
- Copy: `@copywriting`
- Landing pages: `@page-cro`
- SEO: `@seo-fundamentals` + `@seo-audit`
- Email: `@email-sequence`
- Ads: `@paid-ads`
- Launch: `@launch-strategy`

### Planning / architecture / strategy
- Quick plan: `@concise-planning`
- Full plan: `@plan-writing` → `@executing-plans`
- Architecture: `@software-architecture` or `@senior-architect`
- Product strategy: `@product-manager-toolkit`

### Creative / design / visuals
- UI: `@frontend-design`
- Data viz: `@claude-d3js-skill`
- Generative art: `@algorithmic-art`
- Presentations: `@pptx-official`

### Fully autonomous / parallel execution
- Full startup mode: `@loki-mode`
- Independent parallel tasks: `@dispatching-parallel-agents`
- Plan then execute: `@subagent-driven-development`

### Document creation
- Word doc: `@docx-official`
- PDF: `@pdf-official`
- Spreadsheet: `@xlsx-official`
- Presentation: `@pptx-official`

---

## Constraints

- Never recommend more than 1 primary skill and 2 secondary skills at a time.
- Always include the exact `@invoke` syntax so users can copy-paste it.
- If the user's goal spans multiple categories, pick the most upstream skill
  (e.g. `@brainstorming` before `@senior-fullstack`).
- Do not overwhelm the user with the full skill list. Recommend only what is
  relevant to their specific answers.
- If the user is totally lost, default to `@brainstorming` for open-ended
  goals, or `@app-builder` for anything involving building something.
- After recommending, always offer to write a ready-made prompt for them.

---

## Limitations

- Only recommends skills from the installed library. If a skill is not
  installed, the recommendation may not work.
- Routing is based on natural language matching. Highly ambiguous goals
  may require follow-up clarification.
- Does not execute the recommended skill — it only recommends it. The user
  must invoke the skill themselves.
- The routing reference covers the most common skills but does not include
  every skill in the library.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Skill Router"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags skill-router default
```

### Multi-Agent Collaboration

Share outcomes with other agents so the team stays aligned and avoids duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Task completed — results documented and shared with team" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
