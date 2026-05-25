import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import '@unocss/reset/tailwind.css'
import 'virtual:uno.css'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@/components/canvas/node-shared.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
