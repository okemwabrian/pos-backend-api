import { createHash } from "node:crypto";
import { readdir, readFile, writeFile } from "node:fs/promises";
import { join, relative, sep } from "node:path";

const outputDirectory = new URL("./www/", import.meta.url);
const logoSource = new URL("../static/images/free-house-logo.svg", import.meta.url);
const logoTarget = new URL("./www/free-house-logo.svg", import.meta.url);
await writeFile(logoTarget, await readFile(logoSource));
const iconSource = new URL("../static/images/free-house-app-icon.svg", import.meta.url);
const iconTarget = new URL("./www/free-house-app-icon.svg", import.meta.url);
await writeFile(iconTarget, await readFile(iconSource));

async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? listFiles(path) : [path];
  }));
  return nested.flat();
}

const absoluteOutputDirectory = new URL(outputDirectory).pathname;
const files = (await listFiles(absoluteOutputDirectory))
  .filter((path) => !path.endsWith("service-worker.js"))
  .sort();
const fingerprint = createHash("sha256");
for (const path of files) {
  fingerprint.update(relative(absoluteOutputDirectory, path).split(sep).join("/"));
  fingerprint.update(await readFile(path));
}
const cacheName = `chiwas-pos-${fingerprint.digest("hex").slice(0, 16)}`;
const precacheUrls = files.map((path) => (
  `./${relative(absoluteOutputDirectory, path).split(sep).join("/")}`
));

const serviceWorker = `
const CACHE_NAME = ${JSON.stringify(cacheName)};
const PRECACHE_URLS = ${JSON.stringify(precacheUrls)};

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key.startsWith("chiwas-pos-") && key !== CACHE_NAME)
          .map((key) => caches.delete(key)),
      ))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).catch((error) => {
        if (request.mode === "navigate") {
          return caches.match(new URL("./index.html", self.registration.scope).href);
        }
        throw error;
      });
    }),
  );
});
`;

await writeFile(new URL("./www/service-worker.js", import.meta.url), serviceWorker.trimStart());
