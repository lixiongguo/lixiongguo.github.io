const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
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
const nativeChildren = new Map();

const nativeTools = [
  {
    id: "cpu-path-tracing-debug",
    title: "CPU路径追踪调试",
    detail: "本机窗口，并排看 MIS 开和关",
    cwd: path.join(repoRoot, "CPUPathTracing"),
    bin: path.join(repoRoot, "CPUPathTracing", "build", "release", "debug_gui")
  },
  {
    id: "fluid3d",
    title: "流体模拟",
    detail: "本机窗口，自由液面粒子",
    cwd: path.join(repoRoot, "cpp", "Fluid3D"),
    bin: path.join(repoRoot, "cpp", "Fluid3D", "build", "release", "viewer")
  }
];

function nativeCatalog() {
  return nativeTools.map((tool) => ({
    id: tool.id,
    title: tool.title,
    detail: tool.detail,
    state: nativeState(tool.id)
  }));
}

function nativeState(id) {
  const child = nativeChildren.get(id);
  if (child && child.exitCode === null && !child.killed) return "running";
  return "idle";
}

function broadcast(channel, payload) {
  for (const win of BrowserWindow.getAllWindows()) {
    if (!win.isDestroyed()) win.webContents.send(channel, payload);
  }
}

function compileNative(tool) {
  return new Promise((resolve, reject) => {
    const child = spawn("bash", ["build.sh", "gui-build"], { cwd: tool.cwd });
    let err = "";
    child.stderr.on("data", (chunk) => {
      err += chunk.toString();
      if (err.length > 4000) err = err.slice(-4000);
    });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0 && fs.existsSync(tool.bin)) resolve();
      else reject(new Error(err.trim() || "编译失败"));
    });
  });
}

function startNative(tool) {
  const child = spawn(tool.bin, [], { cwd: tool.cwd, stdio: "ignore" });
  nativeChildren.set(tool.id, child);
  child.on("exit", () => {
    if (nativeChildren.get(tool.id) === child) nativeChildren.delete(tool.id);
    broadcast("native-status", {
      id: tool.id,
      state: "idle",
      message: tool.detail
    });
  });
  child.on("error", (err) => {
    broadcast("native-status", {
      id: tool.id,
      state: "idle",
      message: err.message
    });
  });
  broadcast("native-status", {
    id: tool.id,
    state: "running",
    message: "调试窗口已打开"
  });
}

ipcMain.handle("get-demos", () => readyDemos);
ipcMain.handle("get-native-tools", () => nativeCatalog());
ipcMain.handle("launch-native", async (_event, id) => {
  const tool = nativeTools.find((item) => item.id === id);
  if (!tool) return { ok: false, message: "未知工具" };
  if (nativeState(tool.id) === "running") {
    return { ok: true, state: "running", message: "调试窗口已打开" };
  }
  try {
    if (!fs.existsSync(tool.bin)) {
      broadcast("native-status", { id: tool.id, state: "building", message: "正在编译…" });
      await compileNative(tool);
    }
    startNative(tool);
    return { ok: true, state: "running", message: "调试窗口已打开" };
  } catch (err) {
    const message = err && err.message ? err.message : "无法启动";
    broadcast("native-status", { id: tool.id, state: "idle", message: message });
    return { ok: false, state: "idle", message: message };
  }
});

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
  for (const child of nativeChildren.values()) {
    if (child.exitCode === null) child.kill();
  }
  if (server) server.close();
});
