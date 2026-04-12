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
    proxy: {
      // Esto redirige las llamadas de la IA a tu Flask
      '/api': {
        target: 'http://127.0.0.1:10000',
        changeOrigin: true,
        secure: false,
      },
      // Redirige las tareas específicas (corregir_escrito, generar_rap, etc)
      '/explicar': 'http://127.0.0.1:10000',
      '/resumir': 'http://127.0.0.1:10000',
      '/evaluar': 'http://127.0.0.1:10000',
      '/generar_rap': 'http://127.0.0.1:10000',
      '/generar_red': 'http://127.0.0.1:10000',
      '/corregir_escrito': 'http://127.0.0.1:10000',
      '/corregir_resumen': 'http://127.0.0.1:10000',
      '/explicar_concepto': 'http://127.0.0.1:10000',
      '/generar_examen': 'http://127.0.0.1:10000',
      '/evaluar_simulacro': 'http://127.0.0.1:10000',
    },
  },
});
