#!/usr/bin/env node
/**
 * Script to generate installation links for all blueprints.
 * This script will:
 * 1. Get all blueprints from the repository
 * 2. Generate installation links for each blueprint
 */

import { config } from 'dotenv'
import { readFileSync, readdirSync } from 'fs'
import { join } from 'path'
import { parse } from 'yaml'
import { testConnection } from './test-connection'

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
const BLUEPRINTS_DIR = join(process.cwd(), 'blueprints')
const HA_URL = process.env.HA_URL || 'http://supervisor/core'

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
 * Generate installation link for a blueprint
 */
function generateInstallLink(path: string): string {
  const rawUrl = `https://raw.githubusercontent.com/chatondearu/mirabelle-ha-blueprints/main/blueprints/${path}`
  return `${HA_URL}/blueprint/import?url=${encodeURIComponent(rawUrl)}`
}

/**
 * Main function to generate installation links
 */
async function main() {
  // Test connection before proceeding
  if (!await testConnection()) {
    console.error('Failed to connect to Home Assistant. Aborting.')
    process.exit(1)
  }

  console.log('\nGetting blueprints...')
  const blueprints = getBlueprints()
  if (Object.keys(blueprints).length === 0) {
    console.log('No blueprints found')
    process.exit(0)
  }

  console.log(`Found ${Object.keys(blueprints).length} blueprints`)
  console.log('\nInstallation Links:')
  console.log('==================')

  for (const [path, blueprint] of Object.entries(blueprints)) {
    console.log(`\n${blueprint.blueprint.name}`)
    console.log(`Description: ${blueprint.blueprint.description}`)
    console.log(`Type: ${path.split('/')[0]}`)
    console.log(`Install Link: ${generateInstallLink(path)}`)
    console.log('------------------')
  }

  console.log('\nInstructions:')
  console.log('1. Open each installation link in your browser')
  console.log('2. Log in to your Home Assistant instance if prompted')
  console.log('3. Review the blueprint details')
  console.log('4. Click "Import Blueprint" to install')
  console.log('\nNote: Make sure you are logged in to Home Assistant before clicking the links')
}

// Run the script
main().catch((error) => {
  console.error('Fatal error:', error)
  process.exit(1)
})