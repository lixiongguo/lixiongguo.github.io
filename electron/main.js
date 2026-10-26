const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const fs = require("fs");
const path = require("path");
const { createStaticServer, listen } = require("./static-server");

const repoRoot = path.resolve(__dirname, "..");
const docsRoot = path.join(repoRoot, "docs");
const demosPath = path.join(repoRoot, "_data", "algo_demos.yml");
const launcherPath = path.join(__dirname, "launcher.html");

function unquote(value) {
  const text = String(value).trim();
  if (
    (text.startsWith('"') && text.endsWith('"')) ||
    (text.startsWith("'") && text.endsWith("'"))
  ) {
    return text.slice(1, -1);
  }
  return text;
}

function parseReadyDemos(yamlText) {
  const demos = [];
  let current = null;
  for (const line of yamlText.split(/\r?\n/)) {
    if (/^\s*#/.test(line) || line.trim() === "") continue;
    const item = line.match(/^-\s+id:\s*(.+?)\s*$/);
    if (item) {
      if (current) demos.push(current);
      current = { id: unquote(item[1]) };
      continue;
    }
    if (!current) continue;
    const field = line.match(/^  ([A-Za-z0-9_]+):\s*(.*?)\s*$/);
    if (!field) continue;
    current[field[1]] = unquote(field[2]);
  }
  if (current) demos.push(current);
  return demos
    .filter((demo) => {
      return demo.ready === "true" &&
        demo.title &&
        typeof demo.url === "string" &&
        demo.url.startsWith("/") &&
        !demo.url.startsWith("//");
    })
    .map((demo) => ({ title: demo.title, url: demo.url }));
}

let server = null;
let readyDemos = [];
let appPort = 0;

ipcMain.handle("get-demos", () => readyDemos);

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 840,
    show: false,
    title: "算法实验",
    backgroundColor: "#161616",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const target = new URL(url);
      if (target.hostname === "127.0.0.1" && target.port === String(appPort)) {
        win.loadURL(url);
      }
    } catch (err) {
      /* ignore malformed urls */
    }
    return { action: "deny" };
  });

  win.once("ready-to-show", () => win.show());
  win.loadURL("http://127.0.0.1:" + appPort + "/");
  return win;
}

app.whenReady().then(async () => {
  const marker = path.join(docsRoot, "uv-unwrap-simple.html");
  if (!fs.existsSync(marker)) {
    dialog.showErrorBox(
      "缺少构建结果",
      "未找到 docs/uv-unwrap-simple.html。请在仓库根目录运行：JEKYLL_ENV=production bundle exec jekyll build"
    );
    app.quit();
    return;
  }

  readyDemos = parseReadyDemos(fs.readFileSync(demosPath, "utf8"));
  server = createStaticServer({ docsRoot, launcherPath });
  appPort = await listen(server);
  const address = server.address();
  if (!address || address.address !== "127.0.0.1") {
    throw new Error("静态服务必须只监听 127.0.0.1");
  }
  console.log("ALGO_APP_URL http://127.0.0.1:" + appPort + "/");
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
}).catch((err) => {
  console.error(err);
  app.quit();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("will-quit", () => {
  if (server) server.close();
});
