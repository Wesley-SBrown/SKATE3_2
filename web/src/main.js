// web/src/main.js

import { createApp } from 'vue'
import App from './App.vue'

export function initQueryWidget(containerId) {
  const app = createApp(App)
  app.mount(`#${containerId}`)
}