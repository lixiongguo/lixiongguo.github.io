const http = require("http");
const fs = require("fs");
const path = require("path");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".wasm": "application/wasm",
  ".obj": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".map": "application/json; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml"
};

function resolveUnder(root, urlPath) {
  let pathname = urlPath.split("?")[0];
  try {
    pathname = decodeURIComponent(pathname);
  } catch (err) {
    return null;
  }
  if (!pathname.startsWith("/") || pathname.includes("\0")) return null;
  const rootResolved = path.resolve(root);
  const full = path.resolve(rootResolved, "." + pathname);
  if (full !== rootResolved && !full.startsWith(rootResolved + path.sep)) return null;
  return full;
}

function endBody(res, headOnly, text) {
  if (headOnly) res.end();
  else res.end(text);
}

function serveFile(res, filePath, headOnly) {
  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      endBody(res, headOnly, "Not found");
      return;
    }
    const type = MIME[path.extname(filePath).toLowerCase()] || "application/octet-stream";
    res.writeHead(200, {
      "Content-Type": type,
      "Content-Length": stat.size,
      "Cache-Control": "no-cache"
    });
    if (headOnly) {
      res.end();
      return;
    }
    const stream = fs.createReadStream(filePath);
    stream.on("error", () => {
      if (!res.headersSent) res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end();
    });
    stream.pipe(res);
  });
}

function createStaticServer({ docsRoot, launcherPath }) {
  return http.createServer((req, res) => {
    if (req.method !== "GET" && req.method !== "HEAD") {
      res.writeHead(405, { "Content-Type": "text/plain; charset=utf-8" });
      endBody(res, req.method === "HEAD", "Method not allowed");
      return;
    }
    const urlPath = (req.url || "/").split("?")[0];
    const headOnly = req.method === "HEAD";
    if (urlPath === "/") {
      serveFile(res, launcherPath, headOnly);
      return;
    }
    const full = resolveUnder(docsRoot, urlPath);
    if (!full) {
      res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
      endBody(res, headOnly, "Forbidden");
      return;
    }
    serveFile(res, full, headOnly);
  });
}

function listen(server, host = "127.0.0.1") {
  return new Promise((resolve, reject) => {
    const onError = (err) => reject(err);
    server.once("error", onError);
    server.listen(0, host, () => {
      server.removeListener("error", onError);
      const address = server.address();
      resolve(address.port);
    });
  });
}

module.exports = { createStaticServer, listen, MIME, resolveUnder };
