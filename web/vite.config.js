// web/vite.config.js
// builds project as js library to be coupled with Sphinx docs

import { defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

export default defineConfig({
    base: '/SKATE3_2/widget/',
    plugins: [
        vue(),
        nodePolyfills({
            globals: {
                Buffer: true,
                global: true,
                process: true,
            },
            protocolImports: true,
        }),
    ],
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