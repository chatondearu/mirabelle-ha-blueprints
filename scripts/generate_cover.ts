import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs'
import { join } from 'path'
import { parse } from 'yaml'

// Configuration
const TEMPLATES_DIR = join(process.cwd(), 'templates')
const TEMPLATE_FILE = join(TEMPLATES_DIR, 'cover_template.txt')
const DIST_DIR = join(process.cwd(), 'dist')
const OUTPUT_FILE = join(DIST_DIR, 'covers.yaml')

/**
 * Generate cover configuration from template
 */
function generateCoverConfig(name: string, switchEntity: string, travelTime: number): string {
  const coverId = name.toLowerCase().replace(/\s+/g, '_')
  const positionHelper = `input_text.${coverId}_position`
  const directionHelper = `input_text.${coverId}_direction`
  const inputPositionHelperName = `${coverId}_position`
  const inputDirectionHelperName = `${coverId}_direction`

  // Read template
  const template = readFileSync(TEMPLATE_FILE, 'utf8')

  // Replace variables
  const configWithVars = template
    .replace(/{{ cover_id }}/g, coverId)
    .replace(/{{ name }}/g, name)
    .replace(/{{ switch_entity }}/g, switchEntity)
    .replace(/{{ travel_time }}/g, travelTime.toString())
    .replace(/{{ position_helper }}/g, positionHelper)
    .replace(/{{ direction_helper }}/g, directionHelper)
    .replace(/{{ input_position_helper_name }}/g, inputPositionHelperName)
    .replace(/{{ input_direction_helper_name }}/g, inputDirectionHelperName)

  // Validate YAML
  try {
    parse(configWithVars)
    return configWithVars
  } catch (error) {
    console.error('Error validating generated YAML:', error)
    process.exit(1)
  }
}

/**
 * Main function to generate cover configuration
 */
async function main() {
  try {
    // Get command line arguments
    const args = process.argv.slice(2)
    if (args.length !== 3) {
      console.error('Usage: pnpm tsx scripts/generate_cover.ts <name> <switch_entity> <travel_time>')
      console.error('Example: pnpm tsx scripts/generate_cover.ts "Living Room Blind" switch.living_room_blind 30')
      process.exit(1)
    }

    const [name, switchEntity, travelTimeStr] = args
    const travelTime = parseInt(travelTimeStr, 10)

    if (isNaN(travelTime)) {
      console.error('Error: travel_time must be a number')
      process.exit(1)
    }

    // Generate configuration
    const coverConfig = generateCoverConfig(name, switchEntity, travelTime)

    // Create dist directory if it doesn't exist
    if (!existsSync(DIST_DIR)) {
      mkdirSync(DIST_DIR, { recursive: true })
    }

    // Write to file
    writeFileSync(OUTPUT_FILE, coverConfig)
    console.log(`Cover configuration generated successfully in ${OUTPUT_FILE}`)
  } catch (error) {
    console.error('Error generating cover configuration:', error)
    process.exit(1)
  }
}

// Run the script
main() 