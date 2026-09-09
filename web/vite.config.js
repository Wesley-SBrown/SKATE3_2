// web/vite.config.js
// builds project as js library to be coupled with Sphinx docs

import { defineConfig} from 'vite'

export default defineConfig({
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