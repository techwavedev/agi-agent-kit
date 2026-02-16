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
 *   medium - Core + 76 specialized skills + .agent structure
 *   full   - Medium + 782 community skills (complete suite)
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
      "Core + 76 specialized skills + .agent structure (API, Security, Design, AI, Architecture)",
    skills: ["core", "knowledge"],
    includeAgent: true,
  },
  full: {
    name: "Full Suite",
    description:
      "Complete suite (Medium + 782 community skills from antigravity-awesome-skills)",
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
  };

  for (const arg of args) {
    if (arg === "init") {
      options.command = "init";
    } else if (arg.startsWith("--pack=")) {
      options.pack = arg.split("=")[1];
    } else if (arg.startsWith("--path=")) {
      options.path = path.resolve(arg.split("=")[1]);
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
  --no-symlinks    Skip GEMINI.md/CLAUDE.md symlink creation
  --help           Show this help message

${colors.bright}Packs:${colors.reset}
  ${colors.green}core${colors.reset}      Base framework + common skills
           (webcrawler, pdf-reader, qdrant-memory, documentation)

  ${colors.blue}medium${colors.reset}    Core + 76 specialized skills + .agent/ structure
           (API, Security, Design, AI, Architecture, Testing...)
  
  ${colors.yellow}full${colors.reset}      Complete suite (Medium + 782 community skills)
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
      `  2. ${colors.blue}medium${colors.reset}    Core + 76 specialized skills + .agent/ structure`,
    );
    console.log(
      `  3. ${colors.yellow}full${colors.reset}      Complete suite (Medium + 782 community skills)\n`,
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
}

// Create symlinks for multi-platform support
function createSymlinks(targetPath) {
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

  const platformDirs = [
    { platform: ".claude/skills", platformName: "Claude Code" },
    { platform: ".gemini/skills", platformName: "Gemini CLI" },
    { platform: ".codex/skills", platformName: "Codex CLI" },
    { platform: ".cursor/skills", platformName: "Cursor" },
    { platform: ".adal/skills", platformName: "AdaL CLI" },
  ];

  for (const { platform, platformName } of platformDirs) {
    const parts = platform.split("/");
    const parentDir = path.join(targetPath, parts[0]);
    const linkPath = path.join(targetPath, platform);

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
      log.success(`Created skill symlink: ${platform} → skills/ (${platformName})`);
    } catch (err) {
      log.warn(`Failed to create skill symlink for ${platformName}: ${err.message}`);
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

// Main init function
async function init(options) {
  log.header("🚀 AGI Agent Kit Initializer");

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
    createSymlinks(options.path);
  }

  // Copy .agent/ for full pack
  if (PACKS[pack].includeAgent) {
    copyAgentStructure(options.path, templatesPath);
  }

  // Setup Python environment
  setupPythonEnv(options.path);

  // Auto-run platform setup wizard
  runPlatformSetup(options.path);

  // Final message
  log.header("✨ Installation complete!");
  console.log(`
Next steps:
  1. Activate the Python environment:
     ${colors.yellow}source .venv/bin/activate${colors.reset}
  2. Review ${colors.cyan}AGENTS.md${colors.reset} for architecture overview
  3. Boot the memory system (optional, requires Qdrant + Ollama):
     ${colors.yellow}python3 execution/session_boot.py --auto-fix${colors.reset}
  4. Check ${colors.cyan}skills/${colors.reset} for available capabilities
  5. Create ${colors.cyan}.env${colors.reset} with your API keys
  
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
    createSymlinks(options.path);
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
