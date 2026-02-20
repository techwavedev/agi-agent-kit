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
};

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

// Prompt user for pack selection
async function promptPackSelection() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    console.log(
      `\n${colors.bright}Which pack would you like to install?${colors.reset}\n`,
    );
    console.log(
      `  1. ${colors.green}core${colors.reset}      Essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)`,
    );
    console.log(
      `  2. ${colors.blue}medium${colors.reset}    Core + 89 specialized skills + .agent/ structure`,
    );
    console.log(
      `  3. ${colors.yellow}full${colors.reset}      Complete suite (Medium + 785 community skills from antigravity-awesome-skills)\n`,
    );

    rl.question(
      `Enter choice (1-3) or pack name (default: core): `,
      (answer) => {
        rl.close();
        const choice = answer.trim().toLowerCase();

        if (choice === "1" || choice === "core" || choice === "")
          resolve("core");
        else if (
          choice === "2" ||
          choice === "medium" ||
          choice === "knowledge"
        )
          resolve("medium");
        else if (choice === "3" || choice === "full") resolve("full");
        else {
          log.warn("Invalid choice, defaulting to core");
          resolve("core");
        }
      },
    );
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
async function backupExistingFiles(targetPath) {
  // Files and dirs the installer will create/overwrite
  const WATCHED = [
    "AGENTS.md", "GEMINI.md", "CLAUDE.md", "OPENCODE.md",
    "COPILOT.md", "OPENCLAW.md", ".env", "directives",
    "execution", "skills", "skill-creator", ".agent",
  ];

  const existing = WATCHED.filter((f) =>
    fs.existsSync(path.join(targetPath, f)),
  );

  if (existing.length === 0) {
    // Nothing to back up — clean directory
    return;
  }

  console.log(`\n${colors.bright}━━━ Backup Existing Files ━━━${colors.reset}\n`);
  console.log(`  The following items already exist in ${colors.cyan}${targetPath}${colors.reset}`);
  console.log(`  and ${colors.yellow}may be overwritten${colors.reset} by this installer:\n`);
  for (const f of existing) {
    const full = path.join(targetPath, f);
    const isDir = fs.statSync(full).isDirectory();
    console.log(`    ${colors.yellow}${isDir ? "📁" : "📄"} ${f}${colors.reset}`);
  }

  console.log(`
  ${colors.bright}We strongly recommend backing these up before continuing.${colors.reset}`);
  console.log(`  A backup will be saved to: ${colors.cyan}${targetPath}/.agi-backup-<timestamp>/${colors.reset}\n`);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(
      `  Create backup now? (Y/n, default: Y): `,
      (answer) => {
        rl.close();
        const choice = answer.trim().toLowerCase();

        if (choice === "n" || choice === "no") {
          log.warn("Backup skipped. Proceeding without backup — existing files may be overwritten.");
          resolve();
          return;
        }

        // Create timestamped backup dir
        const ts = new Date()
          .toISOString()
          .replace(/[:.]/g, "-")
          .replace("T", "_")
          .slice(0, 19);
        const backupDir = path.join(targetPath, `.agi-backup-${ts}`);
        fs.mkdirSync(backupDir, { recursive: true });

        let backed = 0;
        for (const f of existing) {
          const src = path.join(targetPath, f);
          const dest = path.join(backupDir, f);
          try {
            copyDirSync(src, dest) || fs.copyFileSync(src, dest);
            backed++;
          } catch (e) {
            log.warn(`Could not back up ${f}: ${e.message}`);
          }
        }

        log.success(`Backup created: ${colors.cyan}${backupDir}${colors.reset} (${backed} items)`);
        resolve();
      },
    );
  });
}

// Prompt user for local Qdrant + Ollama usage
async function promptLocalInfrastructure() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    console.log(
      `\n${colors.bright}━━━ Local Memory Infrastructure (Qdrant + Ollama) ━━━${colors.reset}\n`,
    );
    console.log(
      `  This toolkit supports a ${colors.cyan}local vector memory system${colors.reset} powered by:`,
    );
    console.log(
      `    • ${colors.green}Qdrant${colors.reset}  — local vector database for semantic agent memory`,
    );
    console.log(
      `    • ${colors.green}Ollama${colors.reset}  — local LLM runtime for private embeddings (nomic-embed-text)\n`,
    );
    console.log(`  ${colors.yellow}Requirements:${colors.reset} both services must be installed & running locally.`);
    console.log(
      `  If you skip this now, you can enable it later by editing ${colors.cyan}.env${colors.reset}.\n`,
    );
    console.log(`  ${colors.bright}Options:${colors.reset}`);
    console.log(
      `    ${colors.green}1. Yes${colors.reset}   — configure local Qdrant + Ollama (recommended for offline/private use)`,
    );
    console.log(
      `    ${colors.yellow}2. Skip${colors.reset} — disable local memory now (use cloud/API providers only)\n`,
    );

    rl.question(`  Your choice (1/2, default: 1): `, (answer) => {
      rl.close();
      const choice = answer.trim();

      if (choice === "2" || choice.toLowerCase() === "skip" || choice.toLowerCase() === "no" || choice.toLowerCase() === "n") {
        log.info("Local memory infrastructure skipped.");
        resolve({ useLocal: false });
      } else {
        // Default to yes
        log.success("Local Qdrant + Ollama will be configured.");
        resolve({ useLocal: true });
      }
    });
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
  const memoryBlock = [
    "",
    "# ============================================================",
    "# Agent Memory Configuration (Qdrant & Local LLM)",
    "# ============================================================",
    `MEMORY_ENABLED=${memoryEnabled}`,
    "QDRANT_URL=http://localhost:6333",
    "QDRANT_API_KEY=",
    "QDRANT_COLLECTION=agent_memory",
    "EMBEDDING_PROVIDER=ollama",
    "OLLAMA_URL=http://localhost:11434",
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
  log.header(`Installing ${PACKS[pack].name} skills...`);

  const skillGroups = PACKS[pack].skills;

  for (const group of skillGroups) {
    const srcSkillsPath = path.join(templatesPath, "skills", group);
    const destSkillsPath = path.join(targetPath, "skills");

    if (fs.existsSync(srcSkillsPath)) {
      const entries = fs
        .readdirSync(srcSkillsPath, { withFileTypes: true })
        .filter((d) => d.isDirectory());

      for (const entry of entries) {
        const entryPath = path.join(srcSkillsPath, entry.name);

        if (isSkillDir(entryPath)) {
          // Direct skill directory (e.g., core/webcrawler/)
          const dest = path.join(destSkillsPath, entry.name);
          if (copyDirSync(entryPath, dest)) {
            log.success(`Installed skill: ${entry.name}`);
          }
        } else {
          // Category directory (e.g., knowledge/frontend/) — recurse one level
          const categorySkills = fs
            .readdirSync(entryPath, { withFileTypes: true })
            .filter(
              (d) =>
                d.isDirectory() && isSkillDir(path.join(entryPath, d.name)),
            );

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
    return;
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
  }
}

// Main init function
async function init(options) {
  log.header("🚀 AGI Agent Kit Initializer");

  // Ask install scope (project vs global) — skip if already set via CLI flag
  await promptInstallScope(options);

  // Offer to back up any existing files before overwriting
  await backupExistingFiles(options.path);

  // Determine pack
  let pack = options.pack;
  if (!pack) {
    pack = await promptPackSelection();
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
  const infraChoice = await promptLocalInfrastructure();
  writeEnvFile(options.path, infraChoice);

  // If memory enabled, verify Qdrant + Ollama are up and configured
  if (infraChoice.useLocal) {
    verifyMemorySetup(options.path);
  }

  // Auto-run platform setup wizard
  runPlatformSetup(options.path);

  // Final message
  log.header("✨ Installation complete!");

  const memoryHint = infraChoice.useLocal
    ? `  3. ${colors.green}Memory is ENABLED${colors.reset}. Start local services then boot memory system:\n     ${colors.yellow}docker run -p 6333:6333 qdrant/qdrant${colors.reset}  (Qdrant)\n     ${colors.yellow}ollama serve${colors.reset}  (Ollama)\n     ${colors.yellow}python3 execution/session_boot.py --auto-fix${colors.reset}`
    : `  3. ${colors.yellow}Memory is DISABLED${colors.reset}. To enable later, set ${colors.cyan}MEMORY_ENABLED=true${colors.reset} in ${colors.cyan}.env${colors.reset}.`;

  console.log(`
Next steps:
  1. Activate the Python environment:
     ${colors.yellow}source .venv/bin/activate${colors.reset}
  2. Review ${colors.cyan}AGENTS.md${colors.reset} for architecture overview
${memoryHint}
  4. Check ${colors.cyan}skills/${colors.reset} for available capabilities
  5. Extend ${colors.cyan}.env${colors.reset} with any additional API keys
  
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
