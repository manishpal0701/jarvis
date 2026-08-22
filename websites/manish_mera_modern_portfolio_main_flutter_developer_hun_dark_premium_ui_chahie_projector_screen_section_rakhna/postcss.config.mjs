module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
    postcss: {
      plugins: {
        tailwindcss: {},
        autoprefixer: {},
      },
    },
  },
};