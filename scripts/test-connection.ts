#!/usr/bin/env node
/**
 * Script to test the connection to Home Assistant.
 * This script will:
 * 1. Check if the environment variables are set
 * 2. Test the connection to Home Assistant
 * 3. Verify the token is valid
 */

import { config } from 'dotenv'
import axios from 'axios'

// Load environment variables
config()

// Configuration
const HA_URL = process.env.HA_URL || 'http://supervisor/core'
const HA_TOKEN = process.env.HA_TOKEN
const HA_VERIFY_SSL = process.env.HA_VERIFY_SSL !== 'false'
const HA_TIMEOUT = parseInt(process.env.HA_TIMEOUT || '30', 10)

// Cache for connection test result
let connectionTestResult: boolean | null = null

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
 * Test the connection to Home Assistant
 */
export async function testConnection(): Promise<boolean> {
  // Return cached result if available
  if (connectionTestResult !== null) {
    return connectionTestResult
  }

  try {
    console.log('Testing connection to Home Assistant...')
    console.log(`URL: ${HA_URL}`)
    console.log(`SSL Verification: ${HA_VERIFY_SSL ? 'Enabled' : 'Disabled'}`)
    console.log(`Timeout: ${HA_TIMEOUT} seconds`)

    if (!HA_TOKEN) {
      console.error('❌ HA_TOKEN is not set in .env file')
      connectionTestResult = false
      return false
    }

    // Test the connection by getting the Home Assistant version
    const response = await api.get('/api/')

    console.log('Response status:', response.status)
    console.log('Response data:', JSON.stringify(response.data, null, 2))

    if (response.status === 200 && response.data) {
      console.log('✅ Successfully connected to Home Assistant')
      console.log(`Version: ${response.data.version}`)
      connectionTestResult = true
      return true
    } else {
      console.error('❌ Failed to connect to Home Assistant')
      console.error('Status:', response.status)
      console.error('Data:', response.data)
      connectionTestResult = false
      return false
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('❌ Error connecting to Home Assistant:')
      console.error('Status:', error.response?.status)
      console.error('Message:', error.response?.data)
      if (error.code === 'ECONNREFUSED') {
        console.error('Could not connect to Home Assistant. Please check if the URL is correct and Home Assistant is running.')
      } else if (error.response?.status === 401) {
        console.error('Authentication failed. Please check your token.')
      }
    } else {
      console.error('❌ Unexpected error:', error)
    }
    connectionTestResult = false
    return false
  }
}

// Only run the test if this file is executed directly
if (require.main === module) {
  testConnection().then((success) => {
    process.exit(success ? 0 : 1)
  })
} 