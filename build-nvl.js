#!/usr/bin/env node
/**
 * Bundle @neo4j-nvl for same-origin serving (fixes Web Worker init failures).
 * Output: app_console/static/console/js/nvl-bundle.js
 */
const esbuild = require('esbuild');
const path = require('path');

const entry = path.join(__dirname, 'app_console', 'frontend', 'nvl-entry.js');
const outfile = path.join(__dirname, 'app_console', 'static', 'console', 'js', 'nvl-bundle.js');

esbuild
  .build({
    entryPoints: [entry],
    bundle: true,
    format: 'esm',
    outfile,
    target: ['es2020'],
    minify: true,
    sourcemap: false,
    logLevel: 'info',
  })
  .then(() => {
    console.log('NVL bundle built:', outfile);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
