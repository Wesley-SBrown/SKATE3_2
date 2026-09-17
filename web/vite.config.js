// web/vite.config.js
// builds project as js library to be coupled with Sphinx docs

import { defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    build: {
        lib: {
            entry: './src/main.js',
            name: 'QueryWidget',
            fileName: 'query-widget',
            format: ['es']
        },
        outDir: '../docs/source/_static/web',
        emptyOutDir: true,
    }
})