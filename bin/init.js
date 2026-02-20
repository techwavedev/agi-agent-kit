#!/usr/bin/env node
/**
 * agi-agent-kit init
 *
 * CLI tool to scaffold AI agent projects with modular skill packs.
 *
 * Usage:
 *   npx @techwavedev/agi-agent-kit init [--pack=<pack>] [--path=<dir>]
 *
 * Packs:
 *   core   - Base framework + common skills (webcrawler, pdf-reader, qdrant-memory)
 *   medium - Core + 89 specialized skills + .agent structure
 *   full   - Medium + 785 community skills (complete suite)
 *
 * Options:
 *   --path=<dir>    Target directory (default: current)
 *   --no-symlinks   Skip GEMINI.md/CLAUDE.md symlink creation
 *   --help          Show help
 */

const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { execSync } = require("child_process");
const os = require("os");

// Color utilities for terminal output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  cyan: "\x1b[36m",
  red: "\x1b[31m",
};

const log = {
  info: (msg) => console.log(`${colors.cyan}ℹ${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}✔${colors.reset} ${msg}`),
  warn: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✖${colors.reset} ${msg}`),
  header: (msg) =>
    console.log(`\n${colors.bright}${colors.blue}${msg}${colors.reset}\n`),
};

// Pack definitions
const PACKS = {
  core: {
    name: "Core",
    description:
      "Essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)",
    skills: ["core"],
  },
  medium: {
    name: "Medium",
    description:
      "Core + 89 specialized skills + .agent structure (API, Security, Design, AI, Architecture)",
    skills: ["core", "knowledge"],
    includeAgent: true,
  },
  full: {
    name: "Full Suite",
    description:
      "Complete suite (Medium + 785 community skills from antigravity-awesome-skills v5.4.0)",
    skills: ["core", "knowledge", "extended"],
    includeAgent: true,
  },
  custom: {
    name: "Custom",
    description: "Core + selected domains only",
    skills: ["core"], // domains are resolved at install time via options.domains
    includeAgent: true,
  },
};

// Domain definitions — maps domain name to skill counts per tier
const DOMAINS = [
  { id: "ai-agents",      label: "AI Agents & Orchestration", knowledge: 9,   extended: 93  },
  { id: "architecture",  label: "Architecture & System Design", knowledge: 6,   extended: 32  },
  { id: "backend",       label: "Backend & APIs",             knowledge: 8,   extended: 100 },
  { id: "blockchain",    label: "Blockchain & Web3",          knowledge: 1,   extended: 3   },
  { id: "content",       label: "Content & Copy",            knowledge: 6,   extended: 21  },
  { id: "debugging",     label: "Debugging & Observability", knowledge: 5,   extended: 36  },
  { id: "devops",        label: "DevOps & Cloud",            knowledge: 5,   extended: 140 },
  { id: "documentation",label: "Documentation",             knowledge: 3,   extended: 34  },
  { id: "frontend",     label: "Frontend & UI/UX",          knowledge: 11,  extended: 61  },
  { id: "gaming",       label: "Gaming & Creative",         knowledge: 1,   extended: 4   },
  { id: "mobile",       label: "Mobile (iOS/Android/RN)",   knowledge: 1,   extended: 8   },
  { id: "security",     label: "Security & Pen Testing",    knowledge: 2,   extended: 38  },
  { id: "testing",      label: "Testing & QA",             knowledge: 6,   extended: 32  },
  { id: "workflow",     label: "Workflow & Automation",     knowledge: 10,  extended: 142 },
  { id: "i18n",         label: "i18n & Localisation",       knowledge: 1,   extended: 0   },
];

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    command: null,
    pack: null,
    path: process.cwd(),
    symlinks: true,
    help: false,
    global: false,
    ci: false,       // --ci: skip all prompts, use safe defaults
  };

  for (const arg of args) {
    if (arg === "init") {
      options.command = "init";
    } else if (arg.startsWith("--pack=")) {
      options.pack = arg.split("=")[1];
    } else if (arg.startsWith("--path=")) {
      options.path = path.resolve(arg.split("=")[1]);
    } else if (arg === "--global" || arg === "-g") {
      options.global = true;
      options.path = path.join(os.homedir() || process.env.HOME || process.env.USERPROFILE || "", ".agent");
    } else if (arg === "--no-symlinks") {
      options.symlinks = false;
    } else if (arg === "--ci") {
      options.ci = true;
    } else if (arg === "--help" || arg === "-h") {
      options.help = true;
    }
  }

  return options;
}

// Show help message
function showHelp() {
  console.log(`
${colors.bright}agi-agent-kit${colors.reset} - AI Agent Kit Initializer

${colors.bright}Usage:${colors.reset}
  npx @techwavedev/agi-agent-kit init [options]

${colors.bright}Options:${colors.reset}
  --pack=<pack>    Select skill pack (core, medium, full)
  --path=<dir>     Target directory (default: current)
  --global, -g     Install globally to ~/.agent directory
  --no-symlinks    Skip GEMINI.md/CLAUDE.md symlink creation
  --help           Show this help message

${colors.bright}Packs:${colors.reset}
  ${colors.green}core${colors.reset}      Base framework + common skills
           (webcrawler, pdf-reader, qdrant-memory, documentation)

  ${colors.blue}medium${colors.reset}    Core + 89 specialized skills + .agent/ structure
           (API, Security, Design, AI, Architecture, Testing...)
  
  ${colors.yellow}full${colors.reset}      Complete suite (Medium + 785 community skills)
           (All antigravity-awesome-skills, AGI-adapted)

${colors.bright}Examples:${colors.reset}
  npx @techwavedev/agi-agent-kit init
  npx @techwavedev/agi-agent-kit init --pack=medium
  npx @techwavedev/agi-agent-kit init --pack=full

${colors.bright}Note:${colors.reset} Most scripts require ${colors.cyan}python3${colors.reset}.
`);
}

// Prompt user for pack selection (including custom domain picker)
async function promptPackSelection() {
  console.log(`\n${colors.bright}Which pack would you like to install?${colors.reset}\n`);
  console.log(`  ${colors.green}1. core${colors.reset}      — 4 essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)`);
  console.log(`  ${colors.blue}2. medium${colors.reset}    — Core + 89 domain skills + .agent/ structure`);
  console.log(`  ${colors.yellow}3. full${colors.reset}      — Everything: Medium + 785 community skills (878 total)`);
  console.log(`  ${colors.cyan}4. custom${colors.reset}    — Core + you choose specific domains\n`);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  return new Promise((resolve) => {
    rl.question(`  Enter choice (1-4) or pack name (default: core): `, async (answer) => {
      rl.close();
      const choice = answer.trim().toLowerCase();

      if (choice === "2" || choice === "medium" || choice === "knowledge") {
        resolve("medium");
      } else if (choice === "3" || choice === "full") {
        resolve("full");
      } else if (choice === "4" || choice === "custom") {
        const domains = await promptDomainSelection();
        resolve(domains.length > 0 ? "custom" : "core");
      } else {
        if (choice !== "1" && choice !== "core" && choice !== "") {
          log.warn("Invalid choice, defaulting to core");
        }
        resolve("core");
      }
    });
  });
}

// Multi-select domain picker for custom installs
async function promptDomainSelection() {
  const templatesPath = path.join(__dirname, "..", "templates", "skills");

  console.log(`\n${colors.bright}━━━ Custom Domain Selection ━━━${colors.reset}`);
  console.log(`  ${colors.cyan}Core skills (webcrawler, pdf-reader, qdrant-memory, documentation) are always included.${colors.reset}\n`);
  console.log(`  The numbers show ${colors.blue}professional skills${colors.reset} (curated, same as medium pack)`);
  console.log(`  and ${colors.yellow}community skills${colors.reset} (antigravity-awesome-skills, same as full pack).`);
  console.log(`  You get both tiers for each domain you select.\n`);
  console.log(`  ${"".padEnd(38)} ${colors.blue}■ professional${colors.reset}   ${colors.yellow}■ community${colors.reset}`);
  console.log(`  ${"-".repeat(72)}`);

  DOMAINS.forEach((d, i) => {
    const num = String(i + 1).padStart(2);
    const knStr = d.knowledge > 0 ? `${d.knowledge} skills` : `—       `;
    const exStr = d.extended  > 0 ? `${d.extended} skills` : `—`;
    const knColored = d.knowledge > 0
      ? `${colors.blue}+${knStr}${colors.reset}`.padEnd(22)
      : `${colors.dim}${knStr}${colors.reset}`.padEnd(22);
    const exColored = d.extended > 0
      ? `${colors.yellow}+${exStr}${colors.reset}`
      : `${colors.dim}${exStr}${colors.reset}`;
    console.log(`  ${colors.bright}${num}.${colors.reset} ${d.label.padEnd(36)} ${knColored} ${exColored}`);
  });

  console.log(`\n  Enter domain numbers separated by commas, or ranges (e.g. 1,3,5-7,9)`);
  console.log(`  Type ${colors.cyan}all${colors.reset} to select all, or press Enter to skip (core only)\n`);

  const rl2 = readline.createInterface({ input: process.stdin, output: process.stdout });

  return new Promise((resolve) => {
    rl2.question(`  Your domains: `, (answer) => {
      rl2.close();
      const input = answer.trim().toLowerCase();

      if (!input) {
        log.info("No domains selected — core only.");
        resolve([]);
        return;
      }

      if (input === "all") {
        log.success(`All ${DOMAINS.length} domains selected.`);
        // Store selected domain ids on process env for copySkills to read
        process.env._AGI_CUSTOM_DOMAINS = DOMAINS.map((d) => d.id).join(",");
        resolve(DOMAINS.map((d) => d.id));
        return;
      }

      // Parse numbers and ranges like "1,3,5-7"
      const selected = [];
      const parts = input.split(",");
      for (const part of parts) {
        const rangeParts = part.trim().split("-").map(Number);
        if (rangeParts.length === 2) {
          const [from, to] = rangeParts;
          for (let n = from; n <= to; n++) {
            if (n >= 1 && n <= DOMAINS.length) selected.push(DOMAINS[n - 1].id);
          }
        } else {
          const n = parseInt(part.trim(), 10);
          if (n >= 1 && n <= DOMAINS.length) selected.push(DOMAINS[n - 1].id);
        }
      }

      if (selected.length === 0) {
        log.warn("No valid domains selected — falling back to core.");
        resolve([]);
        return;
      }

      const names = selected.map((id) => DOMAINS.find((d) => d.id === id).label);
      log.success(`Selected domains: ${colors.cyan}${names.join(", ")}${colors.reset}`);
      process.env._AGI_CUSTOM_DOMAINS = selected.join(",");
      resolve(selected);
    });
  });
}

// Prompt user for install scope: project-local vs global
async function promptInstallScope(options) {
  // Skip prompt if the user already passed --global or an explicit --path
  if (options.global || options._pathExplicit) {
    return;
  }

  // Platform compatibility reference
  const PLATFORM_COMPAT = [
    { name: "Gemini CLI",   globalDir: "~/.gemini/skills",   globalOk: true,  note: "" },
    { name: "Claude Code",  globalDir: "~/.claude/skills",   globalOk: true,  note: "" },
    { name: "Cursor",       globalDir: "~/.cursor/skills",   globalOk: false, note: "reads skills from project dir only" },
    { name: "Codex CLI",    globalDir: "~/.codex/skills",    globalOk: true,  note: "requires CODEX_HOME env var if non-default" },
    { name: "OpenCode",     globalDir: "(project dir only)", globalOk: false, note: "global skill dirs not yet supported" },
    { name: "OpenClaw",     globalDir: "~/.openclaw/skills", globalOk: true,  note: "" },
    { name: "AdaL CLI",     globalDir: "~/.adal/skills",     globalOk: true,  note: "" },
    { name: "Copilot/VS",   globalDir: "(project dir only)", globalOk: false, note: "skills loaded per-workspace only" },
  ];

  console.log(`\n${colors.bright}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${colors.reset}`);
  console.log(`${colors.bright}  INSTALL SCOPE${colors.reset}`);
  console.log(`${colors.bright}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${colors.reset}\n`);

  console.log(`  ${colors.bright}Option 1 — Project install (default, safest)${colors.reset}`);
  console.log(`  ─────────────────────────────────────────────`);
  console.log(`  Skills and agents are installed inside the ${colors.cyan}current directory${colors.reset}.`);
  console.log(`  Only this project can use them.\n`);
  console.log(`  ${colors.green}✔ Pitfalls to be aware of:${colors.reset}`);
  console.log(`    • You must run init again for every new project`);
  console.log(`    • Skills are NOT shared across projects`);
  console.log(`    • Existing files in this directory ${colors.yellow}may be overwritten${colors.reset} (e.g. AGENTS.md)\n`);

  console.log(`  ${colors.bright}Option 2 — Global install${colors.reset}`);
  console.log(`  ─────────────────────────────────────────────`);
  console.log(`  Skills installed once in ${colors.cyan}~/.agent${colors.reset} and symlinked into`);
  console.log(`  each supported AI platform's global skills directory.\n`);
  console.log(`  ${colors.yellow}⚠ Pitfalls to be aware of:${colors.reset}`);
  console.log(`    • Existing files in platform dirs ${colors.red}may be overwritten${colors.reset}`);
  console.log(`    • Not all platforms support global skill dirs (see table below)`);
  console.log(`    • Symlinks may conflict if you later do a project install`);
  console.log(`    • Removing skills requires manual cleanup of ~/.agent and symlinks\n`);

  console.log(`  ${colors.bright}Platform Global Install Compatibility:${colors.reset}`);
  console.log(`  ${"Platform".padEnd(14)} ${"Global Dir".padEnd(26)} ${"Supported?".padEnd(12)} Notes`);
  console.log(`  ${"─".repeat(72)}`);
  for (const p of PLATFORM_COMPAT) {
    const supported = p.globalOk
      ? `${colors.green}✔ Yes${colors.reset}      `
      : `${colors.red}✖ No${colors.reset}       `;
    const note = p.note ? `${colors.yellow}⚠ ${p.note}${colors.reset}` : "";
    console.log(`  ${p.name.padEnd(14)} ${p.globalDir.padEnd(26)} ${supported} ${note}`);
  }

  console.log(`\n  ${colors.bright}${colors.red}⚠  DISCLAIMER${colors.reset}`);
  console.log(`  ${"─".repeat(60)}`);
  console.log(`  By proceeding you acknowledge that:`);
  console.log(`  • This installer may ${colors.yellow}create, overwrite, or symlink files${colors.reset}`);
  console.log(`    in your project directory or home directory (~/.agent,`);
  console.log(`    ~/.gemini, ~/.claude, ~/.cursor, etc.)`);
  console.log(`  • ${colors.red}Existing AGENTS.md, GEMINI.md, CLAUDE.md${colors.reset} and platform`);
  console.log(`    skill dirs may be replaced.`);
  console.log(`  • The authors of agi-agent-kit ${colors.bright}assume no responsibility${colors.reset}`);
  console.log(`    for data loss, configuration conflicts, or any damages`);
  console.log(`    resulting from using this installer.`);
  console.log(`  • ${colors.cyan}Always back up important files before proceeding.${colors.reset}`);
  console.log(``);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(
      `  Choose install scope (1=Project / 2=Global, default: 1): `,
      (answer) => {
        rl.close();
        const choice = answer.trim();

        if (choice === "2" || choice.toLowerCase() === "global" || choice.toLowerCase() === "g") {
          const os = require("os");
          options.global = true;
          options.path = path.join(os.homedir(), ".agent");
          console.log(``);
          log.warn(`Global install selected. Symlinks will be created in ~/.gemini/skills, ~/.claude/skills, etc.`);
          log.warn(`Platforms marked ✖ above will NOT pick up global skills automatically.`);
          log.success(`Target directory: ${colors.cyan}${options.path}${colors.reset}`);
        } else {
          log.success(`Project install — target: ${colors.cyan}${options.path}${colors.reset}`);
        }
        resolve();
      },
    );
  });
}

// Detect existing files that will be overwritten and offer to back them up
async function backupExistingFiles(targetPath, options = {}) {
  const os = require("os");
  const homeDir = os.homedir();

  // Files and dirs the installer will create/overwrite in the target path
  const WATCHED = [
    "AGENTS.md", "GEMINI.md", "CLAUDE.md", "OPENCODE.md",
    "COPILOT.md", "OPENCLAW.md", ".env", "directives",
    "execution", "skills", "skill-creator", ".agent",
  ];

  // For global installs, also check platform dirs that will be symlinked
  const GLOBAL_PLATFORM_DIRS = options.global ? [
    path.join(homeDir, ".gemini", "skills"),
    path.join(homeDir, ".claude", "skills"),
    path.join(homeDir, ".codex", "skills"),
    path.join(homeDir, ".cursor", "skills"),
    path.join(homeDir, ".openclaw", "skills"),
    path.join(homeDir, ".adal", "skills"),
  ] : [];

  const existing = WATCHED.filter((f) =>
    fs.existsSync(path.join(targetPath, f)),
  );

  const existingGlobalDirs = GLOBAL_PLATFORM_DIRS.filter((p) =>
    fs.existsSync(p) && !fs.lstatSync(p).isSymbolicLink(),
  );

  if (existing.length === 0 && existingGlobalDirs.length === 0) {
    return; // Nothing to back up
  }

  console.log(`\n${colors.bright}━━━ Backup Existing Files ━━━${colors.reset}\n`);
  console.log(`  The following items already exist and ${colors.yellow}may be overwritten${colors.reset}:\n`);

  for (const f of existing) {
    const full = path.join(targetPath, f);
    const isDir = fs.statSync(full).isDirectory();
    console.log(`    ${colors.yellow}${isDir ? "📁" : "📄"} ${full}${colors.reset}`);
  }
  for (const d of existingGlobalDirs) {
    console.log(`    ${colors.yellow}📁 ${d}${colors.reset} ${colors.red}(real dir — will be replaced by symlink)${colors.reset}`);
  }

  console.log(`
  ${colors.bright}We strongly recommend backing these up before continuing.${colors.reset}`);
  const backupBase = options.global
    ? path.join(homeDir, `.agi-global-backup-<timestamp>`)
    : path.join(targetPath, `.agi-backup-<timestamp>`);
  console.log(`  Backup will be saved to: ${colors.cyan}${backupBase}${colors.reset}\n`);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  return new Promise((resolve) => {
    rl.question(`  Create backup now? (Y/n, default: Y): `, (answer) => {
      rl.close();
      const choice = answer.trim().toLowerCase();

      if (choice === "n" || choice === "no") {
        log.warn("Backup skipped — existing files may be overwritten.");
        resolve();
        return;
      }

      const ts = new Date().toISOString().replace(/[:.]/g, "-").replace("T", "_").slice(0, 19);
      const backupDir = options.global
        ? path.join(homeDir, `.agi-global-backup-${ts}`)
        : path.join(targetPath, `.agi-backup-${ts}`);
      fs.mkdirSync(backupDir, { recursive: true });

      let backed = 0;
      for (const f of existing) {
        const src = path.join(targetPath, f);
        const dest = path.join(backupDir, f);
        try { copyDirSync(src, dest) || fs.copyFileSync(src, dest); backed++; } catch (e) {
          log.warn(`Could not back up ${f}: ${e.message}`);
        }
      }
      for (const d of existingGlobalDirs) {
        const name = d.replace(homeDir, "~").replace(/\//g, "_").replace(/^_/, "");
        const dest = path.join(backupDir, name);
        try { copyDirSync(d, dest); backed++; } catch (e) {
          log.warn(`Could not back up ${d}: ${e.message}`);
        }
      }

      log.success(`Backup created: ${colors.cyan}${backupDir}${colors.reset} (${backed} items)`);
      resolve();
    });
  });
}

// Generate an uninstall script for global installs
function generateUninstallScript(installPath, options) {
  const os = require("os");
  const homeDir = os.homedir();
  const scriptPath = path.join(installPath, "uninstall-agi.sh");

  const platformSymlinks = [
    path.join(homeDir, ".gemini", "skills"),
    path.join(homeDir, ".claude", "skills"),
    path.join(homeDir, ".codex", "skills"),
    path.join(homeDir, ".cursor", "skills"),
    path.join(homeDir, ".openclaw", "skills"),
    path.join(homeDir, ".adal", "skills"),
  ];

  const instructionLinks = ["GEMINI.md", "CLAUDE.md", "OPENCODE.md", "COPILOT.md", "OPENCLAW.md"]
    .map((f) => path.join(installPath, f));

  // Build the uninstall script content as a plain string to avoid quote escaping issues
  let script = "#!/usr/bin/env bash\n";
  script += "# AGI Agent Kit - Global Uninstaller\n";
  script += "# Generated: " + new Date().toISOString() + "\n";
  script += "# Install path: " + installPath + "\n";
  script += "\n";
  script += "set -e\n";
  script += "\n";
  script += "echo 'AGI Agent Kit - Global Uninstaller'\n";
  script += "echo 'This will remove:'\n";
  script += "echo '  - Skill symlinks from platform dirs (~/.gemini/skills, ~/.claude/skills, etc.)'\n";
  script += "echo '  - Instruction file symlinks (GEMINI.md, CLAUDE.md, etc.)'\n";
  script += "echo '  - The install directory: " + installPath + "'\n";
  script += "echo ''\n";
  script += "read -r -p 'Proceed? (y/N): ' confirm\n";
  script += "if [ \"$confirm\" != 'y' ] && [ \"$confirm\" != 'Y' ]; then echo 'Aborted.'; exit 0; fi\n";
  script += "\n";
  script += "echo 'Removing platform skill symlinks...'\n";
  for (const p of platformSymlinks) {
    script += "[ -L '" + p + "' ] && rm '" + p + "' && echo '  Removed: " + p + "' || echo '  Skipped (not a symlink): " + p + "'\n";
  }
  script += "\n";
  script += "echo 'Removing instruction file symlinks...'\n";
  for (const p of instructionLinks) {
    script += "[ -L '" + p + "' ] && rm '" + p + "' && echo '  Removed: " + p + "' || echo '  Skipped: " + p + "'\n";
  }
  script += "\n";
  script += "echo 'Removing install directory: " + installPath + "'\n";
  script += "rm -rf '" + installPath + "'\n";
  script += "echo 'AGI Agent Kit global install removed successfully.'\n";
  script += "echo 'Note: your .env and any backups were NOT removed.'\n";

  fs.writeFileSync(scriptPath, script, { mode: 0o755 });
  log.success("Uninstall script created: " + colors.cyan + scriptPath + colors.reset);
  console.log("  Run it anytime to cleanly remove this global install:");
  console.log("    " + colors.yellow + "bash " + scriptPath + colors.reset + "\n");
}

// Prompt user for local Qdrant + Ollama usage
async function promptLocalInfrastructure() {
  // ── Step 1: Detect what's already running ──────────────────────────────────
  const detected = { ollama: false, docker: false, qdrant: false };
  let ollamaUrl = "http://localhost:11434";
  let qdrantUrl = "http://localhost:6333";

  try { execSync("ollama --version", { stdio: "pipe" }); detected.ollama = true; } catch (e) {}
  try { execSync("docker --version",  { stdio: "pipe" }); detected.docker = true; } catch (e) {}
  try {
    execSync(`curl -sf ${qdrantUrl}/healthz`, { stdio: "pipe", timeout: 3000 });
    detected.qdrant = true;
  } catch (e) {}

  const icon  = (ok) => ok ? `${colors.green}✔ detected${colors.reset}` : `${colors.red}✖ not found${colors.reset}`;

  console.log(`\n${colors.bright}━━━ Local Memory Infrastructure (Qdrant + Ollama) ━━━${colors.reset}\n`);
  console.log(`  This toolkit supports a ${colors.cyan}local vector memory system${colors.reset} powered by:`);
  console.log(`    • ${colors.green}Qdrant${colors.reset}  — local vector database for semantic agent memory`);
  console.log(`    • ${colors.green}Ollama${colors.reset}  — local LLM runtime for private embeddings (nomic-embed-text)\n`);
  console.log(`  ${colors.bright}Current status:${colors.reset}`);
  console.log(`    Ollama CLI   ${icon(detected.ollama)}`);
  console.log(`    Docker CLI   ${icon(detected.docker)}`);
  console.log(`    Qdrant API   ${icon(detected.qdrant)} (${qdrantUrl})\n`);

  // ── Step 2: Ask enable/skip ────────────────────────────────────────────────
  const allReady = detected.ollama && detected.qdrant;
  if (allReady) {
    console.log(`  ${colors.green}✔ Both services detected — enabling memory is recommended.${colors.reset}\n`);
  }

  console.log(`  ${colors.bright}1. Yes${colors.reset}   — enable memory (Qdrant + Ollama)`);
  console.log(`  ${colors.bright}2. Skip${colors.reset} — disable for now (can enable later in .env)\n`);

  const answer1 = await _ask(`  Enable memory? (1/2, default: 1): `);
  const wantsMemory = !(answer1 === "2" || ["skip","no","n"].includes(answer1.toLowerCase()));

  if (!wantsMemory) {
    log.info("Memory infrastructure skipped.");
    return { useLocal: false, detected, ollamaUrl, qdrantUrl };
  }

  // ── Step 3: Per-service resolution when not detected ──────────────────────
  if (!detected.ollama) {
    console.log(`\n  ${colors.yellow}⚠  Ollama not detected at localhost.${colors.reset}`);
    console.log(`  ${colors.bright}What would you like to do?${colors.reset}`);
    console.log(`    ${colors.bright}1.${colors.reset} I'll install it locally  → ${colors.cyan}https://ollama.com/download${colors.reset}`);
    console.log(`    ${colors.bright}2.${colors.reset} I have it on a custom URL (remote server / Docker host)\n`);
    const a = await _ask(`  Choice (1/2, default: 1): `);
    if (a === "2") {
      const url = await _ask(`  Enter Ollama URL (e.g. http://192.168.1.10:11434): `);
      if (url.trim()) {
        ollamaUrl = url.trim().replace(/\/$/, "");
        log.success(`Ollama URL set to: ${colors.cyan}${ollamaUrl}${colors.reset}`);
        // Verify it's reachable
        try {
          execSync(`curl -sf ${ollamaUrl}/api/tags`, { stdio: "pipe", timeout: 4000 });
          log.success(`Ollama reachable at ${ollamaUrl}`);
          detected.ollama = true;
        } catch (e) {
          log.warn(`Could not reach Ollama at ${ollamaUrl} — make sure it's running.`);
        }
      }
    } else {
      console.log(`  ${colors.cyan}Install Ollama, then run:${colors.reset} ${colors.yellow}ollama pull nomic-embed-text${colors.reset}`);
      console.log(`  Memory will be written to .env — start Ollama before using the agent.\n`);
    }
  }

  if (!detected.qdrant) {
    console.log(`\n  ${colors.yellow}⚠  Qdrant not detected at ${qdrantUrl}.${colors.reset}`);
    console.log(`  ${colors.bright}What would you like to do?${colors.reset}`);
    console.log(`    ${colors.bright}1.${colors.reset} I'll run it locally via Docker`);
    console.log(`       ${colors.yellow}docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant${colors.reset}`);
    console.log(`    ${colors.bright}2.${colors.reset} I have Qdrant on a custom URL (Qdrant Cloud, remote server, etc.)\n`);
    const a = await _ask(`  Choice (1/2, default: 1): `);
    if (a === "2") {
      const url = await _ask(`  Enter Qdrant URL (e.g. https://xyz.qdrant.tech or http://10.0.0.5:6333): `);
      if (url.trim()) {
        qdrantUrl = url.trim().replace(/\/$/, "");
        const apiKey = await _ask(`  Qdrant API key (leave blank if not required): `);
        log.success(`Qdrant URL set to: ${colors.cyan}${qdrantUrl}${colors.reset}`);
        // Verify
        try {
          const header = apiKey.trim() ? `-H 'api-key: ${apiKey.trim()}'` : "";
          execSync(`curl -sf ${header} ${qdrantUrl}/healthz`, { stdio: "pipe", timeout: 4000 });
          log.success(`Qdrant reachable at ${qdrantUrl}`);
          detected.qdrant = true;
        } catch (e) {
          log.warn(`Could not reach Qdrant at ${qdrantUrl} — check URL and API key.`);
        }
        return { useLocal: true, detected, ollamaUrl, qdrantUrl, qdrantApiKey: apiKey.trim() };
      }
    } else {
      if (!detected.docker) {
        console.log(`\n  ${colors.yellow}⚠  Docker also not found.${colors.reset} Install Docker Desktop first:`);
        console.log(`     ${colors.cyan}https://www.docker.com/products/docker-desktop${colors.reset}`);
      }
      console.log(`  Memory config will be written to .env — start Qdrant before using the agent.\n`);
    }
  }

  log.success("Memory infrastructure configured.");
  return { useLocal: true, detected, ollamaUrl, qdrantUrl };
}

// Helper: promisified readline question
function _ask(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(question, (answer) => { rl.close(); resolve(answer.trim()); });
  });
}

// Write (or merge) a .env file with memory configuration
function writeEnvFile(targetPath, infraChoice) {
  const envPath = path.join(targetPath, ".env");
  const envExamplePath = path.join(
    __dirname,
    "..",
    "templates",
    "base",
    ".env.example",
  );

  // Build the memory block
  const memoryEnabled = infraChoice.useLocal ? "true" : "false";
  const qdrantUrl = infraChoice.qdrantUrl || "http://localhost:6333";
  const qdrantApiKey = infraChoice.qdrantApiKey || "";
  const ollamaUrl = infraChoice.ollamaUrl || "http://localhost:11434";

  const memoryBlock = [
    "",
    "# ============================================================",
    "# Agent Memory Configuration (Qdrant & Local LLM)",
    "# ============================================================",
    `MEMORY_ENABLED=${memoryEnabled}`,
    `QDRANT_URL=${qdrantUrl}`,
    `QDRANT_API_KEY=${qdrantApiKey}`,
    "QDRANT_COLLECTION=agent_memory",
    "EMBEDDING_PROVIDER=ollama",
    `OLLAMA_URL=${ollamaUrl}`,
    "EMBEDDING_MODEL=nomic-embed-text",
    "CACHE_THRESHOLD=0.92",
    "CACHE_TTL_DAYS=7",
    "",
  ].join("\n");

  if (fs.existsSync(envPath)) {
    // .env already exists — append the memory block only if not already present
    const existing = fs.readFileSync(envPath, "utf8");
    if (existing.includes("MEMORY_ENABLED")) {
      // Already configured — patch just the MEMORY_ENABLED line
      const patched = existing.replace(
        /^MEMORY_ENABLED=.*/m,
        `MEMORY_ENABLED=${memoryEnabled}`,
      );
      fs.writeFileSync(envPath, patched, "utf8");
      log.success(`.env updated: MEMORY_ENABLED=${memoryEnabled}`);
    } else {
      // Append the new block
      fs.appendFileSync(envPath, memoryBlock, "utf8");
      log.success(`.env: memory configuration appended (MEMORY_ENABLED=${memoryEnabled})`);
    }
  } else {
    // Create a fresh .env from the example template, then append memory block
    let base = "";
    if (fs.existsSync(envExamplePath)) {
      base = fs.readFileSync(envExamplePath, "utf8");
    } else {
      base = "# AGI Agent Kit — Environment Configuration\n# Fill in your API keys below\n";
    }
    fs.writeFileSync(envPath, base + memoryBlock, "utf8");
    log.success(`.env created (MEMORY_ENABLED=${memoryEnabled})`);
  }
}

// Prompt for update components
async function promptUpdateSelection() {
  return new Promise((resolve) => {
    // For now, update implies updating the Full suite or existing installation
    // We can default to 'full' logic for updates to ensure everything is covered
    resolve("full");
  });
}

// Copy directory recursively
function copyDirSync(src, dest) {
  if (!fs.existsSync(src)) {
    return false;
  }

  fs.mkdirSync(dest, { recursive: true });

  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }

  return true;
}

// Create directory structure
function createStructure(targetPath, options) {
  log.header("Creating directory structure...");

  const dirs = ["directives", "execution", "skills", "skill-creator", ".tmp"];

  for (const dir of dirs) {
    const fullPath = path.join(targetPath, dir);
    fs.mkdirSync(fullPath, { recursive: true });
    log.success(`Created ${dir}/`);
  }
}

// Check if a directory is a skill (has SKILL.md) or a category (contains subdirs)
function isSkillDir(dirPath) {
  return fs.existsSync(path.join(dirPath, "SKILL.md"));
}

// Copy skills based on pack
// Supports both flat (core/) and categorized (knowledge/frontend/react-patterns/) layouts.
// Skills are always installed flat at the destination: skills/<skill-name>/
function copySkills(targetPath, pack, templatesPath) {
  const destSkillsPath = path.join(targetPath, "skills");

  // Helper: install all skills inside a category directory
  function installCategoryDir(categoryPath, categoryName) {
    if (!fs.existsSync(categoryPath)) return 0;
    let count = 0;
    const entries = fs.readdirSync(categoryPath, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const entryPath = path.join(categoryPath, entry.name);
      if (isSkillDir(entryPath)) {
        // Direct skill (e.g. core/webcrawler/)
        const dest = path.join(destSkillsPath, entry.name);
        if (copyDirSync(entryPath, dest)) { count++; }
      } else {
        // Category dir (e.g. knowledge/frontend/) — recurse one level
        const skillDirs = fs.readdirSync(entryPath, { withFileTypes: true })
          .filter((d) => d.isDirectory() && isSkillDir(path.join(entryPath, d.name)));
        for (const skill of skillDirs) {
          const src = path.join(entryPath, skill.name);
          const dest = path.join(destSkillsPath, skill.name);
          if (copyDirSync(src, dest)) { count++; }
        }
      }
    }
    return count;
  }

  if (pack === "custom") {
    // ── Custom pack: always install core, then per-domain selections ──
    log.header("Installing Custom pack (core + selected domains)...");

    // 1. Core skills always
    const coreCount = installCategoryDir(
      path.join(templatesPath, "skills", "core"), "core"
    );
    log.success(`Core: ${coreCount} skills installed`);

    // 2. Selected domains from env (set by promptDomainSelection)
    const selected = (process.env._AGI_CUSTOM_DOMAINS || "").split(",").filter(Boolean);

    if (selected.length === 0) {
      log.warn("No domains selected — core only install.");
      return;
    }

    for (const domainId of selected) {
      let total = 0;
      // Install from knowledge/<domain> if it exists
      const knPath = path.join(templatesPath, "skills", "knowledge", domainId);
      if (fs.existsSync(knPath)) {
        const n = installCategoryDir(knPath, domainId);
        total += n;
      }
      // Install from extended/<domain> if it exists
      const exPath = path.join(templatesPath, "skills", "extended", domainId);
      if (fs.existsSync(exPath)) {
        const n = installCategoryDir(exPath, domainId);
        total += n;
      }
      const domainInfo = DOMAINS.find((d) => d.id === domainId);
      const label = domainInfo ? domainInfo.label : domainId;
      if (total > 0) {
        log.success(`Domain ${colors.cyan}${label}${colors.reset}: ${total} skills installed`);
      } else {
        log.warn(`Domain ${label}: no skills found (check template paths)`);
      }
    }

  } else {
    // ── Standard pack: iterate skill groups ──
    log.header(`Installing ${PACKS[pack].name} skills...`);
    const skillGroups = PACKS[pack].skills;

    for (const group of skillGroups) {
      const srcSkillsPath = path.join(templatesPath, "skills", group);
      if (fs.existsSync(srcSkillsPath)) {
        const entries = fs.readdirSync(srcSkillsPath, { withFileTypes: true })
          .filter((d) => d.isDirectory());

        for (const entry of entries) {
          const entryPath = path.join(srcSkillsPath, entry.name);
          if (isSkillDir(entryPath)) {
            const dest = path.join(destSkillsPath, entry.name);
            if (copyDirSync(entryPath, dest)) {
              log.success(`Installed skill: ${entry.name}`);
            }
          } else {
            const categorySkills = fs.readdirSync(entryPath, { withFileTypes: true })
              .filter((d) => d.isDirectory() && isSkillDir(path.join(entryPath, d.name)));
            for (const skill of categorySkills) {
              const src = path.join(entryPath, skill.name);
              const dest = path.join(destSkillsPath, skill.name);
              if (copyDirSync(src, dest)) {
                log.success(`Installed skill: ${skill.name} (${entry.name})`);
              }
            }
          }
        }
      } else {
        log.warn(`Skills directory not found: ${srcSkillsPath}`);
      }
    }
  }
}

// Copy base files
function copyBaseFiles(targetPath, templatesPath, options) {
  log.header("Copying base files...");

  const baseFiles = [
    { src: "AGENTS.md", dest: "AGENTS.md" },
    { src: ".gitignore", dest: ".gitignore" },
    { src: "requirements.txt", dest: "requirements.txt" },
  ];

  for (const file of baseFiles) {
    const srcPath = path.join(templatesPath, "base", file.src);
    const destPath = path.join(targetPath, file.dest);

    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, destPath);
      log.success(`Created ${file.dest}`);
    }
  }

  // Copy execution scripts (memory system)
  const srcExecution = path.join(templatesPath, "base", "execution");
  const destExecution = path.join(targetPath, "execution");

  if (fs.existsSync(srcExecution)) {
    copyDirSync(srcExecution, destExecution);
    log.success("Installed execution/ (memory system scripts)");
  }

  // Copy directives
  const srcDirectives = path.join(templatesPath, "base", "directives");
  const destDirectives = path.join(targetPath, "directives");

  if (fs.existsSync(srcDirectives)) {
    copyDirSync(srcDirectives, destDirectives);
    log.success("Installed directives/");
  }

  // Copy skill-creator
  const srcSkillCreator = path.join(templatesPath, "base", "skill-creator");
  const destSkillCreator = path.join(targetPath, "skill-creator");

  if (fs.existsSync(srcSkillCreator)) {
    copyDirSync(srcSkillCreator, destSkillCreator);
    log.success("Installed skill-creator/");
  }

  // Copy data (workflows metadata)
  const srcData = path.join(templatesPath, "base", "data");
  const destData = path.join(targetPath, "data");

  if (fs.existsSync(srcData)) {
    copyDirSync(srcData, destData);
    log.success("Installed data/ (workflows metadata)");
  }
}

// Create symlinks for multi-platform support
function createSymlinks(targetPath, options = {}) {
  log.header("Creating symlinks...");

  const agentsMd = path.join(targetPath, "AGENTS.md");

  if (!fs.existsSync(agentsMd)) {
    log.warn("AGENTS.md not found, skipping symlinks");
    return;
  }

  // Instruction file symlinks (all point to AGENTS.md)
  const instructionSymlinks = [
    { name: "GEMINI.md", target: "AGENTS.md" },
    { name: "CLAUDE.md", target: "AGENTS.md" },
    { name: "OPENCODE.md", target: "AGENTS.md" },
    { name: "COPILOT.md", target: "AGENTS.md" },
    { name: "OPENCLAW.md", target: "AGENTS.md" },
  ];

  for (const link of instructionSymlinks) {
    const linkPath = path.join(targetPath, link.name);

    try {
      if (fs.existsSync(linkPath)) {
        fs.unlinkSync(linkPath);
      }
      fs.symlinkSync(link.target, linkPath);
      log.success(`Created symlink: ${link.name} → ${link.target}`);
    } catch (err) {
      log.warn(`Failed to create symlink ${link.name}: ${err.message}`);
    }
  }

  // Platform-specific skill directory symlinks
  // Maps each platform's expected skills path to our canonical skills/ dir
  const skillsDir = path.join(targetPath, "skills");
  if (!fs.existsSync(skillsDir)) {
    return;
  }

  const homeDir = os.homedir() || process.env.HOME || process.env.USERPROFILE || "";

  const platformDirs = [
    { platform: ".claude/skills", platformName: "Claude Code", globalPath: path.join(homeDir, ".claude", "skills") },
    { platform: ".gemini/skills", platformName: "Gemini CLI", globalPath: path.join(homeDir, ".gemini", "skills") },
    { platform: ".codex/skills", platformName: "Codex CLI", globalPath: path.join(process.env.CODEX_HOME || homeDir, ".codex", "skills") },
    { platform: ".cursor/skills", platformName: "Cursor", globalPath: path.join(homeDir, ".cursor", "skills") },
    { platform: ".adal/skills", platformName: "AdaL CLI", globalPath: path.join(homeDir, ".adal", "skills") },
    { platform: ".openclaw/skills", platformName: "OpenClaw", globalPath: path.join(homeDir, ".openclaw", "skills") },
  ];

  for (const info of platformDirs) {
    const { platform, platformName, globalPath } = info;
    const linkPath = options.global ? globalPath : path.join(targetPath, platform);
    const parentDir = path.dirname(linkPath);

    try {
      // Create parent directory (e.g., .claude/)
      fs.mkdirSync(parentDir, { recursive: true });

      if (fs.existsSync(linkPath)) {
        const stat = fs.lstatSync(linkPath);
        if (stat.isSymbolicLink()) {
          fs.unlinkSync(linkPath);
        } else {
          // Real directory — don't overwrite
          continue;
        }
      }

      // Create relative symlink: .claude/skills → ../skills
      const relativeTarget = path.relative(parentDir, skillsDir);
      fs.symlinkSync(relativeTarget, linkPath);
      log.success(
        `Created skill symlink: ${platform} → skills/ (${platformName})`,
      );
    } catch (err) {
      log.warn(
        `Failed to create skill symlink for ${platformName}: ${err.message}`,
      );
    }
  }
}

// Copy .agent/ structure for full pack
function copyAgentStructure(targetPath, templatesPath) {
  log.header("Installing .agent/ structure...");

  const srcAgent = path.join(templatesPath, ".agent");
  const destAgent = path.join(targetPath, ".agent");

  if (fs.existsSync(srcAgent)) {
    copyDirSync(srcAgent, destAgent);
    log.success("Installed .agent/ (agents, workflows, rules)");
  } else {
    log.warn(".agent/ template not found");
  }
}

// Setup Python virtual environment and install dependencies
function setupPythonEnv(targetPath) {
  log.header("Setting up Python environment...");

  const venvPath = path.join(targetPath, ".venv");
  const requirementsPath = path.join(targetPath, "requirements.txt");

  // Skip if venv already exists
  if (fs.existsSync(venvPath)) {
    log.info("Python .venv already exists, skipping creation");
    return;
  }

  // Check if requirements.txt exists
  if (!fs.existsSync(requirementsPath)) {
    log.warn("requirements.txt not found, skipping Python setup");
    return;
  }

  // Detect Python
  let pythonCmd = null;
  for (const cmd of ["python3", "python"]) {
    try {
      execSync(`${cmd} --version`, { stdio: "pipe" });
      pythonCmd = cmd;
      break;
    } catch (e) {
      // try next
    }
  }

  if (!pythonCmd) {
    log.warn("Python not found. Install Python 3.8+ and run:");
    console.log(`     ${colors.yellow}python3 -m venv .venv${colors.reset}`);
    console.log(
      `     ${colors.yellow}source .venv/bin/activate${colors.reset}`,
    );
    console.log(
      `     ${colors.yellow}pip install -r requirements.txt${colors.reset}`,
    );
    return;
  }

  // Create venv
  try {
    log.info(`Creating .venv with ${pythonCmd}...`);
    execSync(`${pythonCmd} -m venv "${venvPath}"`, { stdio: "pipe" });
    log.success("Created .venv/");
  } catch (e) {
    log.warn(`Failed to create venv: ${e.message}`);
    console.log(
      `     Try manually: ${colors.yellow}${pythonCmd} -m venv .venv${colors.reset}`,
    );
    return;
  }

  // Determine pip path (cross-platform)
  const isWindows = process.platform === "win32";
  const pipPath = isWindows
    ? path.join(venvPath, "Scripts", "pip")
    : path.join(venvPath, "bin", "pip");

  // Install dependencies
  try {
    log.info("Installing Python dependencies...");
    execSync(`"${pipPath}" install -r "${requirementsPath}"`, {
      stdio: "pipe",
      timeout: 300000, // 5 min timeout
    });
    log.success("All Python dependencies installed");
  } catch (e) {
    log.warn("Some dependencies may have failed to install");
    console.log(
      `     Run manually: ${colors.yellow}${isWindows ? ".venv\\Scripts\\pip" : ".venv/bin/pip"} install -r requirements.txt${colors.reset}`,
    );
  }

  // Show activation hint
  const activateCmd = isWindows
    ? ".venv\\Scripts\\activate"
    : "source .venv/bin/activate";
  log.info(`Activate with: ${colors.yellow}${activateCmd}${colors.reset}`);
}

// Ask user about platform orchestration features and apply them
async function promptPlatformFeatures(targetPath) {
  const features = { agentTeams: false };

  console.log(`\n${colors.bright}━━━ Platform Orchestration Features ━━━${colors.reset}\n`);
  console.log(`  ${colors.bright}Agent Teams${colors.reset} (Claude Code only)`);
  console.log(`  Enables true parallel multi-agent execution — multiple specialist`);
  console.log(`  agents (frontend, backend, security, etc.) work simultaneously`);
  console.log(`  rather than one at a time. Best for complex, multi-domain tasks.\n`);
  console.log(`  ${colors.yellow}Requires:${colors.reset} Claude Code with experimental features enabled.`);
  console.log(`  ${colors.green}Recommended${colors.reset} if you plan to use @orchestrator or specialist agents.\n`);
  console.log(`  ${colors.bright}1. Enable Agent Teams${colors.reset} — writes to .claude/settings.json (recommended)`);
  console.log(`  ${colors.bright}2. Skip${colors.reset}          — you can enable it manually later\n`);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  return new Promise((resolve) => {
    rl.question(`  Enable Agent Teams? (1/2, default: 1): `, (answer) => {
      rl.close();
      const choice = answer.trim();

      if (choice === "2" || choice.toLowerCase() === "skip" || choice.toLowerCase() === "n") {
        log.info("Agent Teams skipped. Enable later by editing .claude/settings.json.");
        console.log(`  Add this to ${colors.cyan}.claude/settings.json${colors.reset}:`);
        console.log(`    ${colors.yellow}{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }${colors.reset}\n`);
        resolve(features);
        return;
      }

      // Write .claude/settings.json
      try {
        const claudeDir = path.join(targetPath, ".claude");
        fs.mkdirSync(claudeDir, { recursive: true });
        const settingsPath = path.join(claudeDir, "settings.json");

        // Merge with existing settings if present
        let existing = {};
        if (fs.existsSync(settingsPath)) {
          try { existing = JSON.parse(fs.readFileSync(settingsPath, "utf8")); } catch (e) {}
        }
        existing.env = existing.env || {};
        existing.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "1";

        fs.writeFileSync(settingsPath, JSON.stringify(existing, null, 2), "utf8");
        features.agentTeams = true;
        log.success(`Agent Teams enabled → ${colors.cyan}${settingsPath}${colors.reset}`);
        console.log(`  Restart Claude Code in this directory to activate.\n`);
      } catch (e) {
        log.warn(`Could not write .claude/settings.json: ${e.message}`);
      }

      resolve(features);
    });
  });
}

// Auto-run platform setup wizard to pre-configure environment
function runPlatformSetup(targetPath) {
  const setupScript = path.join(
    targetPath,
    "skills",
    "plugin-discovery",
    "scripts",
    "platform_setup.py",
  );

  if (!fs.existsSync(setupScript)) {
    return; // Skill not installed (e.g. core pack)
  }

  log.header("Running platform setup wizard...");

  // Use venv python if available, otherwise system python
  const isWindows = process.platform === "win32";
  const venvPython = isWindows
    ? path.join(targetPath, ".venv", "Scripts", "python")
    : path.join(targetPath, ".venv", "bin", "python3");
  const pythonCmd = fs.existsSync(venvPython) ? `"${venvPython}"` : "python3";

  try {
    const output = execSync(
      `${pythonCmd} "${setupScript}" --project-dir "${targetPath}" --auto`,
      { stdio: "pipe", timeout: 30000 },
    ).toString();

    // Show output
    console.log(output);
  } catch (e) {
    // If --auto flag fails, try with piped stdin
    try {
      const output = execSync(
        `${pythonCmd} "${setupScript}" --project-dir "${targetPath}"`,
        { stdio: "pipe", timeout: 30000, input: "y\n" },
      ).toString();
      console.log(output);
    } catch (e2) {
      log.warn("Platform setup wizard could not auto-run");
      console.log(
        `     Run manually: ${colors.yellow}python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .${colors.reset}`,
      );
    }
  }
}

// Verify memory system (Qdrant + Ollama) after .env is written
function verifyMemorySetup(targetPath) {
  log.header("Verifying memory system (Qdrant + Ollama)...");

  const bootScript = path.join(targetPath, "execution", "session_boot.py");

  if (!fs.existsSync(bootScript)) {
    log.warn("session_boot.py not found — skipping memory verification.");
    console.log(
      `  You can verify later: ${colors.yellow}python3 execution/session_boot.py --auto-fix${colors.reset}`,
    );
    return false;
  }

  const isWindows = process.platform === "win32";
  const venvPython = isWindows
    ? path.join(targetPath, ".venv", "Scripts", "python")
    : path.join(targetPath, ".venv", "bin", "python3");
  const pythonCmd = fs.existsSync(venvPython) ? `"${venvPython}"` : "python3";

  try {
    const output = execSync(
      `${pythonCmd} "${bootScript}" --auto-fix`,
      { stdio: "pipe", timeout: 60000, cwd: targetPath },
    ).toString().trim();
    console.log(`  ${output}`);
    return true;
  } catch (e) {
    // session_boot exits non-zero when services aren't running — show its output
    const output = (e.stdout || e.stderr || "").toString().trim();
    if (output) {
      console.log(`\n${output}\n`);
    }
    console.log(`  ${colors.yellow}⚠  Memory services not detected yet.${colors.reset}`);
    console.log(`
  ${colors.bright}Follow these steps to get Qdrant + Ollama running:${colors.reset}

  ${colors.bright}Step 1 — Install Ollama (if not already installed)${colors.reset}
    ${colors.cyan}https://ollama.com/download${colors.reset}
    Download and install for your OS, then come back here.

  ${colors.bright}Step 2 — Start Ollama in a NEW terminal tab/window${colors.reset}
    ${colors.yellow}ollama serve${colors.reset}
    ${colors.red}⚠ IMPORTANT:${colors.reset} This command runs in the foreground and must stay open.
    Open a new terminal tab (Cmd+T on Mac) and leave this running there.
    You will see logs like "Listening on 127.0.0.1:11434" — that means it's ready.

  ${colors.bright}Step 3 — Start Qdrant via Docker (in your original terminal)${colors.reset}
    ${colors.yellow}docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant${colors.reset}
    The ${colors.cyan}-d${colors.reset} flag runs it in the background. Docker Desktop must be running first.
    Verify it's up: ${colors.yellow}curl http://localhost:6333/healthz${colors.reset}  → should return ${colors.green}{"title":"qdrant"}${colors.reset}

  ${colors.bright}Step 4 — Re-run the memory verification${colors.reset}
    ${colors.yellow}python3 execution/session_boot.py --auto-fix${colors.reset}
    This will pull the embedding model and create the memory collections automatically.
`);
    return false;
  }
}

// Main init function
// Detect an existing AGI Agent Kit install and ask the user what to do
async function detectExistingInstall(targetPath) {
  const agentsMd = path.join(targetPath, "AGENTS.md");
  const versionFile = path.join(targetPath, ".agi-version");

  if (!fs.existsSync(agentsMd)) {
    return { action: "install" }; // Clean install
  }

  // Read installed version if available
  let installedVersion = "unknown";
  if (fs.existsSync(versionFile)) {
    installedVersion = fs.readFileSync(versionFile, "utf8").trim();
  } else {
    // Fallback: try to grep it from AGENTS.md
    const mdContent = fs.readFileSync(agentsMd, "utf8");
    const match = mdContent.match(/agi-agent-kit[\s@v]+([\d.]+)/);
    if (match) installedVersion = match[1];
  }

  // Current package version
  let incomingVersion = "unknown";
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf8"));
    incomingVersion = pkg.version || "unknown";
  } catch (e) {}

  console.log(`\n${colors.bright}━━━ Existing Installation Detected ━━━${colors.reset}\n`);
  console.log(`  ${colors.yellow}AGI Agent Kit is already installed in this directory.${colors.reset}`);
  console.log(`    Installed version : ${colors.cyan}${installedVersion}${colors.reset}`);
  console.log(`    Incoming version  : ${colors.green}${incomingVersion}${colors.reset}\n`);

  const isSameVersion = installedVersion === incomingVersion;
  if (isSameVersion) {
    console.log(`  ${colors.yellow}⚠ Same version detected.${colors.reset} Reinstalling will overwrite current files.\n`);
  } else if (installedVersion !== "unknown" && incomingVersion !== "unknown") {
    const [iMaj, iMin, iPatch] = installedVersion.split(".").map(Number);
    const [nMaj, nMin, nPatch] = incomingVersion.split(".").map(Number);
    const isDowngrade = nMaj < iMaj || (nMaj === iMaj && nMin < iMin) || (nMaj === iMaj && nMin === iMin && nPatch < iPatch);
    if (isDowngrade) {
      console.log(`  ${colors.red}⚠ WARNING: Incoming version is OLDER than installed.${colors.reset}`);
      console.log(`  You are about to downgrade. This may break things.\n`);
    }
  }

  console.log(`  What would you like to do?\n`);
  console.log(`    ${colors.green}1. Update${colors.reset}   — refresh skills, directives & execution scripts`);
  console.log(`              ${colors.cyan}Preserves${colors.reset} your .env, custom skills, and .agent/ folder`);
  console.log(`    ${colors.yellow}2. Reinstall${colors.reset} — full overwrite of all files (${colors.red}destructive${colors.reset})`);
  console.log(`              You will be offered a backup before anything is changed`);
  console.log(`    ${colors.red}3. Cancel${colors.reset}   — abort, make no changes\n`);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  return new Promise((resolve) => {
    rl.question(`  Your choice (1/2/3, default: 1): `, (answer) => {
      rl.close();
      const choice = answer.trim();

      if (choice === "3" || choice.toLowerCase() === "cancel") {
        log.info("Install cancelled.");
        process.exit(0);
      } else if (choice === "2" || choice.toLowerCase() === "reinstall") {
        log.warn("Full reinstall selected — all existing files will be overwritten.");
        resolve({ action: "reinstall", installedVersion, incomingVersion });
      } else {
        // Default: update
        log.success(`Update selected — refreshing to v${incomingVersion}, preserving .env and custom files.`);
        resolve({ action: "update", installedVersion, incomingVersion });
      }
    });
  });
}

async function init(options) {
  log.header("🚀 AGI Agent Kit Initializer");

  if (options.ci) {
    log.info("CI mode: all prompts skipped, using safe defaults (pack=core, memory=disabled, teams=skip).");
  }

  // Detect existing install FIRST — before any scope/pack prompts
  const existingInstall = options.ci
    ? { action: "install" }
    : await detectExistingInstall(options.path);
  const isUpdate = existingInstall.action === "update";

  // Ask install scope (project vs global) — skip if already set via CLI flag
  if (!options.ci) await promptInstallScope(options);

  // Offer backup only for reinstall (update preserves files, and backup is implied)
  if (!isUpdate && !options.ci) {
    await backupExistingFiles(options.path, options);
  }

  // Determine pack
  let pack = options.pack;
  if (!pack) {
    pack = options.ci ? "core" : await promptPackSelection();
  }

  if (!PACKS[pack]) {
    log.error(`Unknown pack: ${pack}`);
    process.exit(1);
  }

  log.info(`Installing ${PACKS[pack].name} pack to: ${options.path}`);

  // Get templates path (relative to this script)
  const templatesPath = path.join(__dirname, "..", "templates");

  if (!fs.existsSync(templatesPath)) {
    log.error("Templates directory not found. Package may be corrupted.");
    process.exit(1);
  }

  // Create structure
  createStructure(options.path, options);

  // Copy base files
  copyBaseFiles(options.path, templatesPath, options);

  // Copy skills
  copySkills(options.path, pack, templatesPath);

  // Create symlinks
  if (options.symlinks) {
    createSymlinks(options.path, options);
  }

  // Copy .agent/ for full pack
  if (PACKS[pack].includeAgent) {
    copyAgentStructure(options.path, templatesPath);
  }

  // Setup Python environment
  setupPythonEnv(options.path);

  // Ask user about local Qdrant + Ollama and write .env
  // Skip on update (preserve existing .env settings)
  let infraChoice = { useLocal: false, detected: {}, ollamaUrl: "http://localhost:11434", qdrantUrl: "http://localhost:6333" };
  if (!isUpdate && !options.ci) {
    infraChoice = await promptLocalInfrastructure();
    writeEnvFile(options.path, infraChoice);
  } else if (!isUpdate && options.ci) {
    // CI: write .env with memory disabled — no Qdrant/Ollama available
    writeEnvFile(options.path, infraChoice);
    log.info("CI mode: memory disabled in .env.");
  } else {
    // On update, read existing MEMORY_ENABLED from .env so hints stay accurate
    const envPath = path.join(options.path, ".env");
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, "utf8");
      const memMatch = envContent.match(/^MEMORY_ENABLED=(.+)$/m);
      infraChoice.useLocal = memMatch && memMatch[1].trim() === "true";
    }
    log.info("Update mode: .env preserved, memory setting unchanged.");
  }

  // If memory enabled, verify Qdrant + Ollama are up and configured
  let memoryVerified = false;
  if (infraChoice.useLocal) {
    memoryVerified = verifyMemorySetup(options.path);
  }

  // Ask about platform features (Agent Teams, MCP, etc.) BEFORE running setup wizard
  const platformFeatures = options.ci
    ? { agentTeams: false }
    : await promptPlatformFeatures(options.path);

  // Auto-run platform setup wizard
  runPlatformSetup(options.path);

  // For global installs: generate an uninstall script
  if (options.global) {
    generateUninstallScript(options.path, options);
  }

  // Write version stamp so future runs can detect the installed version
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf8"));
    fs.writeFileSync(path.join(options.path, ".agi-version"), pkg.version || "unknown", "utf8");
  } catch (e) { /* non-fatal */ }

  // Final message
  const actionLabel = isUpdate ? "🔄 Update complete!" : "✨ Installation complete!";
  log.header(actionLabel);

  let memoryHint;
  if (!infraChoice.useLocal) {
    memoryHint = `  3. ${colors.yellow}Memory is DISABLED${colors.reset}. To enable later, set ${colors.cyan}MEMORY_ENABLED=true${colors.reset} in ${colors.cyan}.env${colors.reset}.`;
  } else if (memoryVerified) {
    // Services were already up and verified during install
    memoryHint = `  3. ${colors.green}✔ Memory is READY${colors.reset} — Qdrant + Ollama verified during setup.\n     Run at any time to check: ${colors.yellow}python3 execution/session_boot.py${colors.reset}`;
  } else {
    // User chose to enable but services weren't up yet
    memoryHint = `  3. ${colors.bright}Start memory services${colors.reset} (open a ${colors.red}NEW terminal tab${colors.reset} for Ollama):\n\n     ${colors.yellow}# Terminal tab 1 — leave this running:${colors.reset}\n     ${colors.yellow}ollama serve${colors.reset}\n\n     ${colors.yellow}# Terminal tab 2 — run once:${colors.reset}\n     ${colors.yellow}docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant${colors.reset}\n     ${colors.yellow}python3 execution/session_boot.py --auto-fix${colors.reset}`;
  }

  console.log(`
${colors.bright}Summary of what was configured:${colors.reset}
  ${colors.green}✔${colors.reset} Python environment (.venv)
  ${colors.green}✔${colors.reset} Skills installed (${pack} pack)
  ${colors.green}✔${colors.reset} AGENTS.md + platform symlinks
  ${infraChoice.useLocal ? colors.green + "✔" + colors.reset : colors.yellow + "−" + colors.reset} Memory (Qdrant + Ollama): ${infraChoice.useLocal ? colors.green + "enabled" + colors.reset : colors.yellow + "disabled" + colors.reset}
  ${platformFeatures.agentTeams ? colors.green + "✔" + colors.reset : colors.yellow + "−" + colors.reset} Agent Teams (parallel execution): ${platformFeatures.agentTeams ? colors.green + "enabled" + colors.reset : colors.yellow + "skipped" + colors.reset}
  ${colors.dim}− MCP Servers: not configured (project-specific, add later)${colors.reset}

${colors.bright}Next steps:${colors.reset}
  1. Activate Python environment:
     ${colors.yellow}source .venv/bin/activate${colors.reset}
  2. Review ${colors.cyan}AGENTS.md${colors.reset} for architecture overview
${memoryHint}${platformFeatures.agentTeams ? "" : `
  ▸ To enable Agent Teams later:\n    ${colors.yellow}echo '${JSON.stringify({ env: { CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1" } }, null, 2)}' > .claude/settings.json${colors.reset}`}
  ▸ To add MCP servers: edit ${colors.cyan}.claude/settings.json${colors.reset} → ${colors.cyan}mcpServers${colors.reset} section
  ▸ To install Claude plugins (pyright-lsp etc): type inside Claude Code:
    ${colors.yellow}/plugin install pyright-lsp@claude-plugins-official${colors.reset}
  ▸ Check ${colors.cyan}skills/${colors.reset} for available capabilities

Happy coding! 🎉
`);
}

// Update function
async function update(options) {
  log.header("🔄 AGI Agent Kit Updater");

  if (!fs.existsSync(path.join(options.path, "AGENTS.md"))) {
    log.error("AGENTS.md not found. Are you in a valid AGI Agent project?");
    log.info('Use "init" to start a new project.');
    process.exit(1);
  }

  // Default to full pack logic for updates to capture all skills/agents
  // Users typically want to update their tooling
  log.info(`Updating framework components in: ${options.path}`);

  const templatesPath = path.join(__dirname, "..", "templates");

  if (!fs.existsSync(templatesPath)) {
    log.error("Templates directory not found.");
    process.exit(1);
  }

  // 1. Update Skills (Core + Knowledge + Extended)
  // Update all skill groups to ensure everything is current
  const skillsToUpdate = ["core", "knowledge", "extended"];
  log.header("Updating Skills...");

  for (const group of skillsToUpdate) {
    const srcSkillsPath = path.join(templatesPath, "skills", group);
    const destSkillsPath = path.join(options.path, "skills");

    if (fs.existsSync(srcSkillsPath)) {
      const skills = fs
        .readdirSync(srcSkillsPath, { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => d.name);

      for (const skill of skills) {
        const src = path.join(srcSkillsPath, skill);
        const dest = path.join(destSkillsPath, skill);

        // Only update extended skills if they already exist in the target
        // (i.e., user has 'full' pack installed)
        if (group === "extended" && !fs.existsSync(dest)) {
          continue; // Skip extended skills not already installed
        }

        if (copyDirSync(src, dest)) {
          console.log(`  ${colors.green}✔${colors.reset} Updated: ${skill}`);
        }
      }
    }
  }

  // 2. Update Agents & Workflows (.agent/)
  log.header("Updating Agents & Workflows...");
  const srcAgent = path.join(templatesPath, ".agent");
  const destAgent = path.join(options.path, ".agent");
  if (fs.existsSync(srcAgent)) {
    if (copyDirSync(srcAgent, destAgent)) {
      console.log(
        `  ${colors.green}✔${colors.reset} Updated .agent/ directory`,
      );
    }
  }

  // 3. Update Skill Creator
  log.header("Updating Skill Creator...");
  const srcSC = path.join(templatesPath, "base", "skill-creator");
  const destSC = path.join(options.path, "skill-creator");
  if (fs.existsSync(srcSC)) {
    copyDirSync(srcSC, destSC);
    console.log(`  ${colors.green}✔${colors.reset} Updated skill-creator/`);
  }

  // 3b. Update Execution Scripts (memory system)
  const srcExec = path.join(templatesPath, "base", "execution");
  const destExec = path.join(options.path, "execution");
  if (fs.existsSync(srcExec)) {
    copyDirSync(srcExec, destExec);
    console.log(
      `  ${colors.green}✔${colors.reset} Updated execution/ (memory system scripts)`,
    );
  }

  // 4. Update Core Documentation if needed
  // We generally respect user's AGENTS.md, but maybe we update GEMINI.md/CLAUDE.md symlinks?
  if (options.symlinks) {
    createSymlinks(options.path, options);
  }

  log.header("✨ Update complete!");
  log.info("Please review any changes to your skills or agents.");
}

// Entry point
async function main() {
  const options = parseArgs();

  if (options.help) {
    showHelp();
    process.exit(0);
  }

  if (
    options.command !== "init" &&
    options.command !== "update" &&
    !options.command
  ) {
    // Default to init if no command specified
    options.command = "init";
  }

  if (options.command === "init") {
    await init(options);
  } else if (options.command === "update") {
    await update(options);
  } else {
    log.error(`Unknown command: ${options.command}`);
    showHelp();
    process.exit(1);
  }
}

main().catch((err) => {
  log.error(`Fatal error: ${err.message}`);
  process.exit(1);
});
