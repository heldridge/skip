module.exports = {
  purge: ["./**/*.j2"],
  mode: 'jit',
  darkMode: 'media',
  theme: {
    extend: {
      spacing: {
        '188': '47rem'
      }
    },
    backgroundColor: theme => ({
      ...theme('colors'),
      'pygmentLight': '#f8f8f8',
      'pygmentDark': '#272822'
    }),
    textColor: theme => ({
      ...theme('colors'),
      'pygmentTextLight': '#f8f8f2'
    })
  },
  variants: {
    extend: {},
  },
  plugins: [],
}
