import { readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const www = join(root, '../custom_components/mirabelle_flow/www')

const indexHtml = readFileSync(join(www, 'index.html'), 'utf-8')
const scriptMatch = indexHtml.match(/\/assets\/(index-[^"]+\.js)/)
const cssMatch = indexHtml.match(/\/assets\/(index-[^"]+\.css)/)

const jsFile = scriptMatch?.[1] ?? readdirSync(join(www, 'assets')).find(f => f.startsWith('index-') && f.endsWith('.js'))
if (!jsFile) {
  console.error('No index bundle found in www/assets')
  process.exit(1)
}

const wrapper = `import("/mirabelle-flow/assets/${jsFile}");
`
writeFileSync(join(www, 'assets', 'panel-wrapper.js'), wrapper, 'utf-8')
console.log('Panel wrapper ->', jsFile)
if (cssMatch) {
  console.log('CSS bundle ->', cssMatch[1])
}
