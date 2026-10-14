import { cp, mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const webBuild = fileURLToPath(new URL("./www/", import.meta.url));
const windowsBundle = fileURLToPath(new URL("../release/windows/portable-pos/", import.meta.url));

await rm(windowsBundle, { recursive: true, force: true });
await mkdir(windowsBundle, { recursive: true });
await cp(webBuild, windowsBundle, { recursive: true });
console.log(`Prepared standalone Windows POS web bundle in ${windowsBundle}`);
