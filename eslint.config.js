const stylistic = require('@stylistic/eslint-plugin')
const globals = require('globals')

module.exports = [
    {
        plugins: {
            '@stylistic': stylistic,
        },
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'commonjs',
            globals: {
                ...globals.browser,
                ...globals.commonjs,
                ...globals.mocha,
            },
        },
        rules: {
            'block-scoped-var': 'error',
            'camelcase': 'off',
            'class-methods-use-this': 'error',
            'consistent-return': 'error',
            'default-case': 'error',
            'default-case-last': 'error',
            'default-param-last': 'error',
            'grouped-accessor-pairs': 'error',
            'no-caller': 'error',
            'no-console': 'error',
            'no-empty-function': 'error',
            'no-eval': 'error',
            'no-labels': 'error',
            'no-new': 'error',
            'no-new-func': 'error',
            'no-new-wrappers': 'error',
            'no-script-url': 'error',
            'no-self-compare': 'error',
            'no-shadow': 'error',
            'no-throw-literal': 'error',
            'no-undefined': 'error',
            'no-unreachable-loop': 'error',
            'no-unused-expressions': 'off',
            'no-useless-backreference': 'error',
            'no-useless-concat': 'error',
            'no-var': 'error',
            'prefer-const': 'error',
            'prefer-promise-reject-errors': 'error',
            'require-atomic-updates': 'error',
            'require-await': 'error',
            'yoda': 'error',

            // Stylistic rules moved out of ESLint core in v9 into @stylistic.
            '@stylistic/array-bracket-spacing': 'error',
            '@stylistic/block-spacing': 'error',
            '@stylistic/brace-style': 'error',
            '@stylistic/indent': ['error', 4, { SwitchCase: 0 }],
            '@stylistic/linebreak-style': ['error', 'unix'],
            '@stylistic/max-len': ['error', { code: 120 }],
            '@stylistic/no-extra-parens': 'error',
            '@stylistic/object-curly-spacing': ['error', 'always', { arraysInObjects: true }],
            '@stylistic/quotes': ['error', 'single'],
            '@stylistic/semi': ['error', 'never'],
        },
    },
]
