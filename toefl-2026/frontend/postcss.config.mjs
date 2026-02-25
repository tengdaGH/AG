/** @type {import('postcss-load-config').Config} */
const config = {
    plugins: {
        '@tailwindcss/postcss': {},
        autoprefixer: {}, // You may add CSS nesting or other plugins here over time
    },
};

export default config;
