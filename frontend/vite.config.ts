import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // The project uses a single .env at the repo root (see essentials.md #11
  // and .env.example) covering the backend, pipeline, and frontend --
  // Vite defaults to looking in its own root (frontend/), so point it one
  // level up instead of duplicating env values into a second file.
  envDir: path.resolve(import.meta.dirname, '..'),
})
