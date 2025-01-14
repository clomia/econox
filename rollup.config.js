import { spawn } from "child_process";
import svelte from "rollup-plugin-svelte";
import commonjs from "@rollup/plugin-commonjs";
import terser from "@rollup/plugin-terser";
import resolve from "@rollup/plugin-node-resolve";
import livereload from "rollup-plugin-livereload";
import css from "rollup-plugin-css-only";
import json from "@rollup/plugin-json";
import sveltePreprocess from "svelte-preprocess";
import typescript from "@rollup/plugin-typescript";
import replace from "@rollup/plugin-replace";
import execute from "rollup-plugin-execute";
import polyfillNode from "rollup-plugin-polyfill-node";

const production = !process.env.ROLLUP_WATCH;

function serve() {
  let server;

  function toExit() {
    if (server) server.kill(0);
  }

  return {
    writeBundle() {
      if (server) return;
      server = spawn("npm", ["run", "start", "--", "--dev"], {
        stdio: ["ignore", "inherit", "inherit"],
        shell: true,
      });

      process.on("SIGTERM", toExit);
      process.on("exit", toExit);
    },
  };
}

export default {
  input: "frontend/main.ts",
  output: {
    sourcemap: true,
    format: "es",
    name: "app",
    dir: 'frontend/static/build'
  },
  plugins: [
    replace({
      "process.env.NODE_ENV": JSON.stringify("production"),
      preventAssignment: true,
    }),
    svelte({
      preprocess: sveltePreprocess({ sourceMap: !production }),
      compilerOptions: {
        // enable run-time checks when not in production
        dev: !production,
      },
    }),
    // we'll extract any component CSS out into
    // a separate file - better for performance
    css({ output: "bundle.css" }),
    json(),

    execute("python script/ui_text_dts.py", { once: false }), // UiText.yaml에 대한 Type 정의 자동 생성
    typescript({
      sourceMap: !production,
      inlineSources: !production,
    }),

    // If you have external dependencies installed from
    // npm, you'll most likely need these plugins. In
    // some cases you'll need additional configuration -
    // consult the documentation for details:
    // https://github.com/rollup/plugins/tree/master/packages/commonjs
    resolve({
      browser: true,
      dedupe: ["svelte"],
      exportConditions: ["svelte"],
    }),
    commonjs(),
    polyfillNode(),

    // In dev mode, call `npm run start` once
    // the bundle has been generated
    !production && serve(),

    // Watch the `public` directory and refresh the
    // browser on changes when not in production
    !production && livereload("public"),

    // If we're building for production (npm run build
    // instead of npm run dev), minify
    production && terser(),
  ],
  watch: {
    clearScreen: false,
  },
  onwarn: (warning, warn) => {
    // polyfill-node & semver 순환 의존성 경고 필터링
    // (예기치 못한 동작이 있는경우 이거 비활성화 하고 경고 보기)
    if (warning.code === "CIRCULAR_DEPENDENCY") {
      return;
    }
    // Typescript sourceMap 관련 경고 필터링
    if (warning.plugin === "typescript" && /sourceMap/.test(warning.message)) {
      return;
    }
    // 나머지 경고는 출력
    warn(warning);
  },
};
