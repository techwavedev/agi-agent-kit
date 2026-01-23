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
 * 
 * Options:
 *   --path=<dir>    Target directory (default: current)
 *   --no-symlinks   Skip GEMINI.md/CLAUDE.md symlink creation
 *   --help          Show help
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Color utilities for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  red: '\x1b[31m'
};

const log = {
  info: (msg) => console.log(`${colors.cyan}ℹ${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}✔${colors.reset} ${msg}`),
  warn: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✖${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bright}${colors.blue}${msg}${colors.reset}\n`)
};

// Pack definitions
const PACKS = {
  core: {
    name: 'Core',
    description: 'Essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)',
    skills: ['core']
  }
};

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    command: null,
    pack: null,
    path: process.cwd(),
    symlinks: true,
    help: false
  };

  for (const arg of args) {
    if (arg === 'init') {
      options.command = 'init';
    } else if (arg.startsWith('--pack=')) {
      options.pack = arg.split('=')[1];
    } else if (arg.startsWith('--path=')) {
      options.path = path.resolve(arg.split('=')[1]);
    } else if (arg === '--no-symlinks') {
      options.symlinks = false;
    } else if (arg === '--help' || arg === '-h') {
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
  --pack=<pack>    Select skill pack (core, ec, full)
  --path=<dir>     Target directory (default: current)
  --no-symlinks    Skip GEMINI.md/CLAUDE.md symlink creation
  --help           Show this help message

${colors.bright}Packs:${colors.reset}
  ${colors.green}core${colors.reset}   Base framework + common skills
         (webcrawler, pdf-reader, qdrant-memory, documentation)

${colors.bright}Examples:${colors.reset}
  npx @techwavedev/agi-agent-kit init
  npx @techwavedev/agi-agent-kit init --pack=core

${colors.bright}Note:${colors.reset} Most scripts require ${colors.cyan}python3${colors.reset}.
`);
}

// Prompt user for pack selection
async function promptPackSelection() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    console.log(`\n${colors.bright}Which pack would you like to install?${colors.reset}\n`);
    console.log(`  1. ${colors.green}core${colors.reset}  - Essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)`);

    rl.question(`Enter choice (1) or pack name (default: core): `, (answer) => {
      rl.close();
      const choice = answer.trim().toLowerCase();
      
      if (choice === '1' || choice === 'core' || choice === '') resolve('core');
      else {
        log.warn('Invalid choice, defaulting to core');
        resolve('core');
      }
    });
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
  log.header('Creating directory structure...');
  
  const dirs = [
    'directives',
    'execution',
    'skills',
    'skill-creator',
    '.tmp'
  ];
  
  for (const dir of dirs) {
    const fullPath = path.join(targetPath, dir);
    fs.mkdirSync(fullPath, { recursive: true });
    log.success(`Created ${dir}/`);
  }
}

// Copy skills based on pack
function copySkills(targetPath, pack, templatesPath) {
  log.header(`Installing ${PACKS[pack].name} skills...`);
  
  const skillGroups = PACKS[pack].skills;
  
  for (const group of skillGroups) {
    const srcSkillsPath = path.join(templatesPath, 'skills', group);
    const destSkillsPath = path.join(targetPath, 'skills');
    
    if (fs.existsSync(srcSkillsPath)) {
      const skills = fs.readdirSync(srcSkillsPath, { withFileTypes: true })
        .filter(d => d.isDirectory())
        .map(d => d.name);
      
      for (const skill of skills) {
        const src = path.join(srcSkillsPath, skill);
        const dest = path.join(destSkillsPath, skill);
        
        if (copyDirSync(src, dest)) {
          log.success(`Installed skill: ${skill}`);
        }
      }
    } else {
      log.warn(`Skills directory not found: ${srcSkillsPath}`);
    }
  }
}

// Copy base files
function copyBaseFiles(targetPath, templatesPath, options) {
  log.header('Copying base files...');
  
  const baseFiles = [
    { src: 'AGENTS.md', dest: 'AGENTS.md' },
    { src: '.gitignore', dest: '.gitignore' },
    { src: 'requirements.txt', dest: 'requirements.txt' }
  ];
  
  for (const file of baseFiles) {
    const srcPath = path.join(templatesPath, 'base', file.src);
    const destPath = path.join(targetPath, file.dest);
    
    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, destPath);
      log.success(`Created ${file.dest}`);
    }
  }
  
  // Copy skill-creator
  const srcSkillCreator = path.join(templatesPath, 'base', 'skill-creator');
  const destSkillCreator = path.join(targetPath, 'skill-creator');
  
  if (fs.existsSync(srcSkillCreator)) {
    copyDirSync(srcSkillCreator, destSkillCreator);
    log.success('Installed skill-creator/');
  }
}

// Create symlinks
function createSymlinks(targetPath) {
  log.header('Creating symlinks...');
  
  const agentsMd = path.join(targetPath, 'AGENTS.md');
  
  if (!fs.existsSync(agentsMd)) {
    log.warn('AGENTS.md not found, skipping symlinks');
    return;
  }
  
  const symlinks = [
    { name: 'GEMINI.md', target: 'AGENTS.md' },
    { name: 'CLAUDE.md', target: 'AGENTS.md' }
  ];
  
  for (const link of symlinks) {
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
}

// Copy .agent/ structure for full pack
function copyAgentStructure(targetPath, templatesPath) {
  log.header('Installing .agent/ structure...');
  
  const srcAgent = path.join(templatesPath, '.agent');
  const destAgent = path.join(targetPath, '.agent');
  
  if (fs.existsSync(srcAgent)) {
    copyDirSync(srcAgent, destAgent);
    log.success('Installed .agent/ (agents, workflows, rules)');
  } else {
    log.warn('.agent/ template not found');
  }
}

// Main init function
async function init(options) {
  log.header('🚀 AGI Agent Kit Initializer');
  
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
  const templatesPath = path.join(__dirname, '..', 'templates');
  
  if (!fs.existsSync(templatesPath)) {
    log.error('Templates directory not found. Package may be corrupted.');
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
  
  // Final message
  log.header('✨ Installation complete!');
  console.log(`
Next steps:
  1. Review ${colors.cyan}AGENTS.md${colors.reset} for architecture overview
  2. Install Python dependencies:
     ${colors.yellow}pip install requests beautifulsoup4 html2text lxml qdrant-client${colors.reset}
  3. Check ${colors.cyan}skills/${colors.reset} for available capabilities
  4. Create ${colors.cyan}.env${colors.reset} with your API keys
  
Happy coding! 🎉
`);
}

// Entry point
async function main() {
  const options = parseArgs();
  
  if (options.help) {
    showHelp();
    process.exit(0);
  }
  
  if (options.command !== 'init' && !options.command) {
    // Default to init if no command specified
    options.command = 'init';
  }
  
  if (options.command === 'init') {
    await init(options);
  } else {
    log.error(`Unknown command: ${options.command}`);
    showHelp();
    process.exit(1);
  }
}

main().catch(err => {
  log.error(`Fatal error: ${err.message}`);
  process.exit(1);
});
