/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app_console/templates/**/*.html',
    './app_console/static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        sidebar: '#1f2937',
      },
    },
  },
  plugins: [],
};
