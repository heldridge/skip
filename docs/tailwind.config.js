module.exports = {
  purge: {
    content: ["./**/*.j2"],
    /* Safelist for menu-button toggling */
    safelist: ["bg-black", "dark:bg-gray-100", "text-gray-100", "dark:text-black"]
  },
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
