// Plugins
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import ViteFonts from 'unplugin-fonts/vite'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vite-plugin
    vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    ViteFonts({
      google: {
        families: [{
          name: 'Roboto',
          styles: 'wght@100;300;400;500;700;900',
        }],
      },
    }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    host:'0.0.0.0',
    port: 63100,
    proxy: {
      '/query': {
        target: 'http://47.106.252.91:63001',
        // target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/query_full_mode/, ''),
      },
      '/get_meta': {
        target: 'http://47.106.252.91:63001',
        // target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/get_meta/, ''),
      },
    },
  },
})
