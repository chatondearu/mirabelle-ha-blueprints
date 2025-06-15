#!/usr/bin/env node
/**
 * Script to automatically update all automations in Home Assistant.
 * This script will:
 * 1. Get all blueprints from the repository
 * 2. Get all automations from Home Assistant
 * 3. Update automations that match the blueprints
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

interface Automation {
  id: string
  name: string
  input: Record<string, any>
}

// Configuration
const HA_URL = process.env.HA_URL || 'http://supervisor/core'
const HA_TOKEN = process.env.HA_TOKEN
const HA_VERIFY_SSL = process.env.HA_VERIFY_SSL !== 'false'
const HA_TIMEOUT = parseInt(process.env.HA_TIMEOUT || '30', 10)
const BLUEPRINTS_DIR = join(process.cwd(), 'blueprints', 'automations')

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
 * Get headers for Home Assistant API requests
 */
function getHeaders(): Record<string, string> {
  if (!HA_TOKEN) {
    throw new Error('HA_TOKEN environment variable is not set')
  }
  return {
    Authorization: `Bearer ${HA_TOKEN}`,
    'Content-Type': 'application/json',
  }
}

/**
 * Get all blueprints from the repository
 */
function getBlueprints(): Record<string, Blueprint> {
  const blueprints: Record<string, Blueprint> = {}
  const files = readdirSync(BLUEPRINTS_DIR)

  for (const file of files) {
    if (file.endsWith('.yaml')) {
      try {
        const content = readFileSync(join(BLUEPRINTS_DIR, file), 'utf8')
        const blueprint = parse(content) as Blueprint
        if (blueprint?.blueprint?.name?.startsWith('[CDA]')) {
          blueprints[blueprint.blueprint.name] = blueprint
        }
      } catch (error) {
        console.error(`Error loading blueprint ${file}:`, error)
      }
    }
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
    console.error('Error getting automations:', error)
    throw error
  }
}

/**
 * Update an automation with a blueprint
 */
async function updateAutomation(automationId: string, blueprint: Blueprint): Promise<boolean> {
  try {
    // Get current automation
    const response = await api.get(`/api/services/automation/get/${automationId}`)
    const currentAutomation = response.data

    // Update automation with blueprint
    const updateData = {
      blueprint,
      automation_id: automationId,
      input: currentAutomation.input || {},
    }

    await api.post('/api/services/automation/reload', updateData)
    return true
  } catch (error) {
    console.error(`Error updating automation ${automationId}:`, error)
    return false
  }
}

/**
 * Main function to update all automations
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

  console.log('Getting automations...')
  try {
    const automations = await getAutomations()
    let updated = 0

    for (const automation of automations) {
      const name = automation.name || ''
      if (name.startsWith('[CDA]')) {
        const blueprintName = name.split(']')[1].trim()
        if (blueprintName in blueprints) {
          console.log(`Updating automation: ${name}`)
          if (await updateAutomation(automation.id, blueprints[blueprintName])) {
            updated++
          }
        }
      }
    }

    console.log(`\nUpdated ${updated} automations`)
  } catch (error) {
    console.error('Error:', error)
    process.exit(1)
  }
}

// Run the script
main().catch((error) => {
  console.error('Fatal error:', error)
  process.exit(1)
}) 