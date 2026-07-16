#!/usr/bin/env node

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const DEFAULT_CONFIG = path.join(os.homedir(), '.config', 'mcp', 'mcp.json');
const DEFAULT_SOURCE = 'git+https://github.com/appunni-m/coverage-mcp.git@main';

function usage() {
  return `Usage: install-pi-mcp.mjs [--config <path>] [--source <git-requirement>]

Adds or updates coverage-mcp in a shared Pi MCP configuration without
replacing other servers or top-level settings.
`;
}

function parseArgs(args) {
  const options = {
    configPath: DEFAULT_CONFIG,
    source: DEFAULT_SOURCE,
  };

  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === '--help' || argument === '-h') {
      return { help: true, ...options };
    }
    if (argument !== '--config' && argument !== '--source') {
      throw new Error(`Unknown argument: ${argument}`);
    }

    const value = args[index + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Missing value for ${argument}`);
    }
    index += 1;

    if (argument === '--config') {
      options.configPath = value;
    } else {
      options.source = value;
    }
  }

  return { help: false, ...options };
}

function readConfig(configPath) {
  if (!fs.existsSync(configPath)) {
    return {};
  }

  let config;
  try {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (error) {
    throw new Error(`Cannot parse MCP config ${configPath}: ${error.message}`);
  }

  if (!config || typeof config !== 'object' || Array.isArray(config)) {
    throw new Error(`MCP config must contain a JSON object: ${configPath}`);
  }
  if (
    config.mcpServers !== undefined &&
    (!config.mcpServers ||
      typeof config.mcpServers !== 'object' ||
      Array.isArray(config.mcpServers))
  ) {
    throw new Error(`mcpServers must contain a JSON object: ${configPath}`);
  }
  return config;
}

function validateSource(value) {
  if (!value.startsWith('git+https://')) {
    throw new Error(`Coverage MCP source must use git+https: ${value}`);
  }
  return value;
}

function install({ configPath, source }) {
  const resolvedPath = path.resolve(configPath);
  const config = readConfig(resolvedPath);
  config.mcpServers ??= {};
  config.mcpServers['coverage-mcp'] = {
    command: 'uvx',
    args: ['--from', validateSource(source), 'coverage-mcp', 'connect'],
    lifecycle: 'lazy',
  };

  fs.mkdirSync(path.dirname(resolvedPath), { recursive: true });
  const temporaryPath = `${resolvedPath}.${process.pid}.tmp`;
  try {
    fs.writeFileSync(temporaryPath, `${JSON.stringify(config, null, 2)}\n`, {
      mode: 0o600,
    });
    fs.renameSync(temporaryPath, resolvedPath);
  } finally {
    if (fs.existsSync(temporaryPath)) {
      fs.unlinkSync(temporaryPath);
    }
  }
  console.log(`Configured coverage-mcp in ${resolvedPath}`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(usage());
  } else {
    install(options);
  }
} catch (error) {
  console.error(error.message);
  console.error(usage());
  process.exitCode = 1;
}
