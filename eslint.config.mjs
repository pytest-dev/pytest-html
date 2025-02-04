import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [...compat.extends("google"), {
    languageOptions: {
        globals: {
            ...globals.browser,
            ...globals.commonjs,
        },
        ecmaVersion: "latest",
        sourceType: "script",
    },

    rules: {
        "array-bracket-spacing": "error",
        "block-scoped-var": "error",
        "block-spacing": "error",
        "brace-style": "error",
        camelcase: "off",
        "class-methods-use-this": "error",
        "consistent-return": "error",
        "default-case": "error",
        "default-case-last": "error",
        "default-param-last": "error",
        "grouped-accessor-pairs": "error",
        indent: ["error", 4],
        "linebreak-style": ["error", "unix"],
        "max-len": ["error", {
            code: 120,
        }],
        "no-caller": "error",
        "no-console": "error",
        "no-empty-function": "error",
        "no-eval": "error",
        "no-extra-parens": "error",
        "no-labels": "error",
        "no-new": "error",
        "no-new-func": "error",
        "no-new-wrappers": "error",
        "no-return-await": "error",
        "no-script-url": "error",
        "no-self-compare": "error",
        "no-shadow": "error",
        "no-throw-literal": "error",
        "no-undefined": "error",
        "no-unreachable-loop": "error",
        "no-unused-expressions": "off",
        "no-useless-backreference": "error",
        "no-useless-concat": "error",
        "no-var": "error",
        "object-curly-spacing": ["error", "always", {
            arraysInObjects: true,
        }],
        "prefer-const": "error",
        "prefer-promise-reject-errors": "error",
        "require-atomic-updates": "error",
        "require-await": "error",
        "require-jsdoc": 0,
        semi: ["error", "never"],
        quotes: ["error", "single"],
        yoda: "error",
    },
}];
