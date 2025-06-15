#!/usr/bin/env node
/**
 * Script to install all blueprints in Home Assistant.
 * This script will:
 * 1. Get all blueprints from the repository
 * 2. Install them in Home Assistant using the API
 */

import { config } from 'dotenv'
import { readFileSync, readdirSync } from 'fs'
import { join } from 'path'
import { parse } from 'yaml'
import axios from 'axios'

// Load environment variables
config()

// Types
interface Blueprint {
  blueprint: {
    name: string
    description: string
    domain: string
    input: Record<string, any>
  }
}

// Configuration
const HA_URL = process.env.HA_URL || 'http://supervisor/core'
const HA_TOKEN = process.env.HA_TOKEN
const HA_VERIFY_SSL = process.env.HA_VERIFY_SSL !== 'false'
const HA_TIMEOUT = parseInt(process.env.HA_TIMEOUT || '30', 10)
const BLUEPRINTS_DIR = join(process.cwd(), 'blueprints')

// Axios instance with default config
const api = axios.create({
  baseURL: HA_URL,
  headers: {
    Authorization: `Bearer ${HA_TOKEN}`,
    'Content-Type': 'application/json',
  },
  timeout: HA_TIMEOUT * 1000,
  httpsAgent: HA_VERIFY_SSL ? undefined : new (require('https').Agent)({ rejectUnauthorized: false }),
})

/**
 * Get all blueprints from the repository
 */
function getBlueprints(): Record<string, Blueprint> {
  const blueprints: Record<string, Blueprint> = {}
  const domains = ['automations', 'scripts', 'scenes', 'dashboards']

  for (const domain of domains) {
    const domainPath = join(BLUEPRINTS_DIR, domain)
    try {
      const files = readdirSync(domainPath)
      for (const file of files) {
        if (file.endsWith('.yaml')) {
          try {
            const content = readFileSync(join(domainPath, file), 'utf8')
            const blueprint = parse(content) as Blueprint
            if (blueprint?.blueprint?.name?.startsWith('[CDA]')) {
              blueprints[`${domain}/${file}`] = blueprint
            }
          } catch (error) {
            console.error(`Error loading blueprint ${file}:`, error)
          }
        }
      }
    } catch (error) {
      console.error(`Error reading directory ${domain}:`, error)
    }
  }

  return blueprints
}

/**
 * Install a blueprint in Home Assistant
 */
async function installBlueprint(path: string, blueprint: Blueprint): Promise<boolean> {
  try {
    const domain = path.split('/')[0]
    const response = await api.post(`/api/services/${domain}/import_blueprint`, {
      url: `https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/${path}`,
    })
    return response.status === 200
  } catch (error) {
    console.error(`Error installing blueprint ${path}:`, error)
    return false
  }
}

/**
 * Main function to install all blueprints
 */
async function main() {
  if (!HA_TOKEN) {
    console.error('Please set the HA_TOKEN environment variable in .env file')
    process.exit(1)
  }

  console.log(`Using Home Assistant URL: ${HA_URL}`)
  console.log(`SSL Verification: ${HA_VERIFY_SSL ? 'Enabled' : 'Disabled'}`)
  console.log(`Timeout: ${HA_TIMEOUT} seconds`)

  console.log('\nGetting blueprints...')
  const blueprints = getBlueprints()
  if (Object.keys(blueprints).length === 0) {
    console.log('No blueprints found')
    process.exit(0)
  }

  console.log(`Found ${Object.keys(blueprints).length} blueprints`)
  let installed = 0

  for (const [path, blueprint] of Object.entries(blueprints)) {
    console.log(`\nInstalling blueprint: ${blueprint.blueprint.name}`)
    if (await installBlueprint(path, blueprint)) {
      console.log('✅ Successfully installed')
      installed++
    } else {
      console.log('❌ Failed to install')
    }
  }

  console.log(`\nInstalled ${installed} out of ${Object.keys(blueprints).length} blueprints`)
}

// Run the script
main().catch((error) => {
  console.error('Fatal error:', error)
  process.exit(1)
}) 