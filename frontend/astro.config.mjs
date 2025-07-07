import { defineConfig } from 'astro/config';
import tailwindcss from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'http://localhost:8082/',
  base: '/', // Add this line for correct base path
  integrations: [sitemap(), tailwindcss()],
  vite: {
  },
});
