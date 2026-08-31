import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Copy the logo from the secure artifact directory directly into the public folder
const src = 'C:/Users/RUTHRESH.J.P/.gemini/antigravity-ide/brain/a18674b6-edb0-4c28-8746-16de98d0f6e9/autofir_logo_1788102955592.jpg'
const destDir = path.resolve(__dirname, 'public')
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true })
}
if (fs.existsSync(src)) {
  fs.copyFileSync(src, path.join(destDir, 'logo.jpg'))
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})
