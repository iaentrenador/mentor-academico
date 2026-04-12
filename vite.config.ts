import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    // En desarrollo local, redirige todas las llamadas /api/ al backend Flask
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:10000',
        changeOrigin: true,
        secure: false,
      },
      '/login': 'http://127.0.0.1:10000',
      '/callback': 'http://127.0.0.1:10000',
      '/logout': 'http://127.0.0.1:10000',
    },
  },
});
