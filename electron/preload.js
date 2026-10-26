const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("algoApp", {
  getDemos: () => ipcRenderer.invoke("get-demos")
});

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

window.addEventListener("DOMContentLoaded", mountBackButton);
