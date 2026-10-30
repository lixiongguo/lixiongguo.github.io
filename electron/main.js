const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const { createStaticServer, listen } = require("./static-server");
const { createProfiler } = require("./profile");

const repoRoot = path.resolve(__dirname, "..");
const labRoot = path.resolve(repoRoot, "..");
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
let profiler = null;
let latestProfile = null;
const nativeChildren = new Map();

function existingDir(candidates) {
  for (const dir of candidates) {
    if (fs.existsSync(dir)) return dir;
  }
  return candidates[0];
}

// Windows 上本机实验是 Linux 二进制（WSL + WSLg），需要把 Windows 路径换成
// WSL 能识别的 /mnt/<drive>/... 形式，并通过 wsl 启动。
const isWindows = process.platform === "win32";

function toWslPath(winPath) {
  const text = String(winPath).replace(/\//g, "\\");
  const match = text.match(/^([A-Za-z]):\\(.*)$/);
  if (!match) return text.replace(/\\/g, "/");
  return "/mnt/" + match[1].toLowerCase() + "/" + match[2].replace(/\\/g, "/");
}

function quoteShell(text) {
  return '"' + String(text).replace(/"/g, '\\"') + '"';
}

function toolAvailable(tool) {
  return fs.existsSync(tool.cwd) && fs.existsSync(path.join(tool.cwd, "build.sh"));
}

const cpuProject = existingDir([
  path.join(labRoot, "CPUPathTracing"),
  path.join(repoRoot, "CPUPathTracing")
]);
const curvatureProject = existingDir([
  path.join(labRoot, "ddg-exercises", "projects", "principal-curvature-field"),
  path.join(repoRoot, "cpp", "ddg-exercises", "projects", "principal-curvature-field")
]);

const nativeTools = [
  {
    id: "cpu-path-tracing-debug",
    title: "CPU路径追踪调试",
    detail: "本机窗口，焦散透镜场景",
    cwd: cpuProject,
    bin: path.join(cpuProject, "build", "release", "debug_gui")
  },
  {
    id: "fluid3d",
    title: "流体模拟",
    detail: "本机窗口，自由液面粒子",
    cwd: path.join(repoRoot, "cpp", "Fluid3D"),
    bin: path.join(repoRoot, "cpp", "Fluid3D", "build", "release", "viewer")
  },
  {
    id: "principal-curvature-field",
    title: "主曲率场",
    detail: "QuadCover 主曲率，可换模型",
    cwd: curvatureProject,
    bin: path.join(curvatureProject, "build", "bin", "main")
  },
  {
    id: "quad-meshing",
    title: "四边形网格",
    detail: "本机窗口，可换模型，跑朴素合并 / MIQ / QuadCover",
    cwd: curvatureProject,
    bin: path.join(curvatureProject, "build", "bin", "quad_test")
  },
  {
    id: "simple-param",
    title: "简单参数化",
    detail: "本机平面窗口，下拉选择算法；粉红线是切缝，点开模型可改",
    cwd: curvatureProject,
    bin: path.join(curvatureProject, "build", "bin", "simple_param")
  },
  {
    id: "cone-unwrap",
    title: "锥奇异点展开",
    detail: "左右两个视图，点「展开」才计算 Circle Pattern / CETM / Ricci / Incremental Flattening",
    cwd: curvatureProject,
    bin: path.join(curvatureProject, "build", "bin", "cone_unwrap")
  },
  {
    id: "hof-unwrap",
    title: "全纯1-形式",
    detail: "左右两个视图，点「展开」才计算。粉红线是 C++ tree-cotree 割缝",
    cwd: curvatureProject,
    bin: path.join(curvatureProject, "build", "bin", "hof_unwrap")
  }
];

function nativeCatalog() {
  return nativeTools.map((tool) => {
    const available = toolAvailable(tool);
    return {
      id: tool.id,
      title: tool.title,
      detail: available ? tool.detail : "源码目录缺失，无法构建",
      available,
      state: available ? nativeState(tool.id) : "unavailable"
    };
  });
}

function nativeState(id) {
  const child = nativeChildren.get(id);
  if (child && child.exitCode === null && !child.killed) return "running";
  return "idle";
}

function runningTools() {
  const tools = [];
  for (const [id, child] of nativeChildren) {
    if (!child || child.exitCode !== null || child.killed) continue;
    const tool = nativeTools.find((item) => item.id === id);
    tools.push({ id, title: tool ? tool.title : id, pid: child.pid });
  }
  return tools;
}

function broadcast(channel, payload) {
  for (const win of BrowserWindow.getAllWindows()) {
    if (!win.isDestroyed()) win.webContents.send(channel, payload);
  }
}

function compileNative(tool) {
  return new Promise((resolve, reject) => {
    let child;
    if (isWindows) {
      const script = "cd " + quoteShell(toWslPath(tool.cwd)) + " && ./build.sh gui-build";
      child = spawn("wsl", ["--", "bash", "-lc", script]);
    } else {
      child = spawn("bash", ["build.sh", "gui-build"], { cwd: tool.cwd });
    }
    let err = "";
    child.stderr.on("data", (chunk) => {
      err += chunk.toString();
      if (err.length > 4000) err = err.slice(-4000);
    });
    child.stdout.on("data", () => { /* keep the pipe drained */ });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0 && fs.existsSync(tool.bin)) resolve();
      else reject(new Error(err.trim() || "编译失败"));
    });
  });
}

function startNative(tool) {
  let child;
  if (isWindows) {
    console.log("[native] wsl start:", tool.id);
    // 程序靠相对路径找场景/资源，所以先 cd 到工程目录再 exec。
    const script = "cd " + quoteShell(toWslPath(tool.cwd)) + " && exec " + quoteShell(toWslPath(tool.bin));
    child = spawn("wsl", ["--", "bash", "-lc", script], { stdio: "ignore" });
  } else {
    child = spawn(tool.bin, [], { cwd: tool.cwd, stdio: "ignore" });
  }
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

ipcMain.handle("get-profile", () => latestProfile);
ipcMain.handle("get-demos", () => readyDemos);
ipcMain.handle("get-native-tools", () => nativeCatalog());
ipcMain.handle("launch-native", async (_event, id) => {
  const tool = nativeTools.find((item) => item.id === id);
  if (!tool) return { ok: false, message: "未知工具" };
  if (!toolAvailable(tool)) {
    return { ok: false, state: "unavailable", message: "源码目录缺失，无法构建" };
  }
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
  const marker = path.join(docsRoot, "index.html");
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
  profiler = createProfiler({
    getAppMetrics: () => app.getAppMetrics(),
    getTools: runningTools
  });
  profiler.start((sample) => {
    latestProfile = sample;
    broadcast("profile-sample", sample);
  });
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
  if (profiler) profiler.stop();
  for (const child of nativeChildren.values()) {
    if (child.exitCode === null) child.kill();
  }
  if (server) server.close();
});
