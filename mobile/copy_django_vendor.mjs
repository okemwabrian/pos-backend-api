import { cpSync, mkdirSync, copyFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const mobileRoot = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(mobileRoot, "node_modules");
const staticRoot = resolve(mobileRoot, "../static/vendor");

function copy(source, destination) {
  const output = resolve(staticRoot, destination);
  mkdirSync(dirname(output), { recursive: true });
  copyFileSync(resolve(packageRoot, source), output);
}

copy("bootstrap/dist/css/bootstrap.min.css", "bootstrap/bootstrap.min.css");
copy("bootstrap/dist/js/bootstrap.bundle.min.js", "bootstrap/bootstrap.bundle.min.js");
copy("@fortawesome/fontawesome-free/css/all.min.css", "fontawesome/css/all.min.css");
cpSync(
  resolve(packageRoot, "@fortawesome/fontawesome-free/webfonts"),
  resolve(staticRoot, "fontawesome/webfonts"),
  { recursive: true },
);
copy("chart.js/dist/chart.umd.min.js", "chart.js/chart.umd.min.js");
copy("html5-qrcode/html5-qrcode.min.js", "html5-qrcode.min.js");
copy("bootstrap/LICENSE", "licenses/bootstrap.txt");
copy("@fortawesome/fontawesome-free/LICENSE.txt", "licenses/fontawesome-free.txt");
copy("chart.js/LICENSE.md", "licenses/chart.js.md");
copy("html5-qrcode/LICENSE", "licenses/html5-qrcode.txt");

console.log("Copied offline vendor assets and license notices into static/vendor.");
