module.exports = {
  purge: ["./**/*.j2"],
  mode: 'jit',
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {
      spacing: {
        '188': '47rem'
      }
    },
  },
  variants: {
    extend: {},
  },
  plugins: [],
}
