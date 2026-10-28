import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const host = env.LAN_HOST ?? 'localhost'
  const apiPort = env.API_PORT ?? '8000'

  return {
    envDir: '..',
    server: {
      host: '0.0.0.0',
      port: Number(env.FRONTEND_PORT ?? '5173'),
    },
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(`http://${host}:${apiPort}`),
    },
    plugins: [react()],
  }
})
