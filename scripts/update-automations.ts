#!/usr/bin/env node
/**
 * Script to generate update links for automations.
 * This script will:
 * 1. Get all automations from Home Assistant
 * 2. Generate update links for automations that match our blueprints
 */

import { config } from 'dotenv'
import { readFileSync, readdirSync } from 'fs'
import { join } from 'path'
import { parse } from 'yaml'
import axios from 'axios'
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

interface Automation {
  id: string
  name: string
  source_file: string
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
  const domainPath = join(BLUEPRINTS_DIR, 'automations')

  try {
    const files = readdirSync(domainPath)
    for (const file of files) {
      if (file.endsWith('.yaml')) {
        try {
          const content = readFileSync(join(domainPath, file), 'utf8')
          const blueprint = parse(content) as Blueprint
          if (blueprint?.blueprint?.name?.startsWith('[CDA]')) {
            blueprints[file] = blueprint
          }
        } catch (error) {
          console.error(`Error loading blueprint ${file}:`, error)
        }
      }
    }
  } catch (error) {
    console.error(`Error reading directory automations:`, error)
  }

  return blueprints
}

/**
 * Get all automations from Home Assistant
 */
async function getAutomations(): Promise<Automation[]> {
  try {
    const response = await api.get('/api/services/automation/list')
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error getting automations:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
      })
    } else {
      console.error('Error getting automations:', error)
    }
    return []
  }
}

/**
 * Generate update link for an automation
 */
function generateUpdateLink(automation: Automation): string {
  return `${HA_URL}/config/automation/edit/${automation.id}`
}

/**
 * Main function to generate update links
 */
async function main() {
  if (!HA_TOKEN) {
    console.error('Please set the HA_TOKEN environment variable in .env file')
    process.exit(1)
  }

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

  console.log('\nGetting automations from Home Assistant...')
  const automations = await getAutomations()
  if (automations.length === 0) {
    console.log('No automations found')
    process.exit(0)
  }

  // Filter automations that start with [CDA]
  const cdaAutomations = automations.filter(automation =>
    automation.name.startsWith('[CDA]')
  )

  console.log(`\nFound ${cdaAutomations.length} [CDA] automations`)
  console.log('\nUpdate Links:')
  console.log('============')

  for (const automation of cdaAutomations) {
    console.log(`\n${automation.name}`)
    console.log(`Source: ${automation.source_file}`)
    console.log(`Update Link: ${generateUpdateLink(automation)}`)
    console.log('------------------')
  }

  console.log('\nInstructions:')
  console.log('1. Open each update link in your browser')
  console.log('2. Log in to your Home Assistant instance if prompted')
  console.log('3. Review the automation details')
  console.log('4. Click "Save" to update the automation')
  console.log('\nNote: Make sure you are logged in to Home Assistant before clicking the links')
}

// Run the script
main().catch((error) => {
  console.error('Fatal error:', error)
  process.exit(1)
}) 