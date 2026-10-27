const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("algoApp", {
  getDemos: () => ipcRenderer.invoke("get-demos"),
  getNativeTools: () => ipcRenderer.invoke("get-native-tools"),
  launchNative: (id) => ipcRenderer.invoke("launch-native", id),
  onNativeStatus: (callback) => {
    ipcRenderer.on("native-status", (_event, status) => callback(status));
  },
  getProfile: () => ipcRenderer.invoke("get-profile"),
  onProfile: (callback) => {
    ipcRenderer.on("profile-sample", (_event, sample) => callback(sample));
  }
});

function coreText(percent) {
  const cores = Math.max(0, percent) / 100;
  return (cores >= 10 ? cores.toFixed(0) : cores.toFixed(1)) + " 核";
}

function mountProfile() {
  if (location.pathname === "/") return;
  if (document.getElementById("algo-profile")) return;
  const style = document.createElement("style");
  style.textContent = [
    "#algo-profile{position:fixed;top:12px;right:12px;z-index:2147483646;width:280px;",
    "background:rgba(16,16,16,.92);color:#f2f2f2;border:1px solid rgba(255,255,255,.16);",
    "border-radius:8px;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;",
    "box-shadow:0 8px 24px rgba(0,0,0,.28)}",
    "#algo-profile button{width:100%;text-align:left;background:transparent;color:#ffd7ad;",
    "border:0;padding:8px 10px;cursor:pointer;font:inherit}",
    "#algo-profile .body{padding:0 10px 10px}",
    "#algo-profile.collapsed .body{display:none}",
    "#algo-profile .row{color:#d0d0d0;margin-bottom:4px}",
    "#algo-profile .tool{color:#fff}",
    "#algo-profile .cores{display:flex;align-items:flex-end;gap:3px;height:36px;margin:6px 0 8px}",
    "#algo-profile .core{flex:1;height:100%;display:flex;align-items:flex-end;background:#2a2a2a;border-radius:2px}",
    "#algo-profile .core i{display:block;width:100%;background:#e87d0d;border-radius:2px}"
  ].join("");
  document.documentElement.appendChild(style);

  const panel = document.createElement("aside");
  panel.id = "algo-profile";
  if (sessionStorage.getItem("algo-profile-collapsed") === "1") panel.classList.add("collapsed");
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.textContent = "资源";
  const body = document.createElement("div");
  body.className = "body";
  const cores = document.createElement("div");
  cores.className = "cores";
  const mem = document.createElement("div");
  mem.className = "row";
  const appRow = document.createElement("div");
  appRow.className = "row";
  const tools = document.createElement("div");
  body.append(cores, mem, appRow, tools);
  panel.append(toggle, body);
  document.documentElement.appendChild(panel);

  toggle.addEventListener("click", () => {
    panel.classList.toggle("collapsed");
    sessionStorage.setItem("algo-profile-collapsed", panel.classList.contains("collapsed") ? "1" : "0");
  });

  function paintCores(loads) {
    if (cores.childElementCount !== loads.length) {
      cores.replaceChildren();
      loads.forEach(() => {
        const cell = document.createElement("div");
        cell.className = "core";
        cell.appendChild(document.createElement("i"));
        cores.appendChild(cell);
      });
    }
    loads.forEach((load, index) => {
      const cell = cores.children[index];
      const pct = Math.round(load * 100);
      cell.title = "核 " + (index + 1) + "  " + pct + "%";
      cell.firstChild.style.height = Math.max(2, Math.round(load * 36)) + "px";
    });
    cores.dataset.loads = loads.map((load) => Math.round(load * 100)).join(",");
  }

  function fmt(sample) {
    if (!sample || !sample.coreCpu) {
      toggle.textContent = "资源";
      return;
    }
    const busy = sample.coreCpu.filter((load) => load >= 0.5).length;
    toggle.textContent = "资源  " + busy + "/" + sample.coreCpu.length + " 核忙";
    paintCores(sample.coreCpu);
    mem.textContent = "内存 " + sample.memUsedGB.toFixed(1) + " / " + sample.memTotalGB.toFixed(1) + " GB";
    appRow.textContent = "本窗口  " + coreText(sample.appCpu) + "   " + Math.round(sample.appRssMB) + " MB";
    tools.replaceChildren();
    (sample.tools || []).forEach((tool) => {
      const line = document.createElement("div");
      line.className = "tool";
      line.textContent = tool.alive
        ? tool.title + "  " + coreText(tool.cpu) + "   " + Math.round(tool.rssMB) + " MB"
        : tool.title + "  已退出";
      tools.appendChild(line);
    });
  }

  ipcRenderer.invoke("get-profile").then(fmt).catch(() => {});
  ipcRenderer.on("profile-sample", (_event, sample) => fmt(sample));
}

function mountBackButton() {
  if (location.pathname === "/") return;
  if (document.getElementById("algo-app-back")) return;
  const button = document.createElement("button");
  button.id = "algo-app-back";
  button.type = "button";
  button.textContent = "返回列表";
  button.style.cssText = [
    "position:fixed",
    "left:12px",
    "bottom:12px",
    "z-index:2147483647",
    "background:rgba(20,20,20,0.9)",
    "color:#f3f3f3",
    "border:1px solid rgba(255,255,255,0.22)",
    "border-radius:6px",
    "padding:7px 12px",
    "font:600 13px/1.2 'Segoe UI',system-ui,sans-serif",
    "cursor:pointer"
  ].join(";");
  button.addEventListener("click", () => {
    location.assign("/");
  });
  document.body.appendChild(button);
}

window.addEventListener("DOMContentLoaded", () => {
  mountBackButton();
  mountProfile();
});
