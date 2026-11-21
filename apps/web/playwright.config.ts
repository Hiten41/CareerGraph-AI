import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'e2e',timeout:150000,use:{channel:process.env.BROWSER_CHANNEL||'chromium',viewport:{width:1440,height:960}}});
