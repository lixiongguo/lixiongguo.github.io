/**
 * Lazy WASM module loader for GitHub Pages / Jekyll.
 */
(function (global) {
  const WASM_BASE = 'assets/wasm/';
  const _loadedScripts = {};
  const _instances = {};

  function loadScript(url) {
    if (_loadedScripts[url]) return _loadedScripts[url];
    _loadedScripts[url] = new Promise(function (resolve, reject) {
      const s = document.createElement('script');
      s.src = url;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('Failed to load ' + url)); };
      document.head.appendChild(s);
    });
    return _loadedScripts[url];
  }

  async function loadWasmModule(name, factoryName, extraConfig) {
    const key = name + '::' + factoryName;
    if (_instances[key]) return _instances[key];
    await loadScript(WASM_BASE + name + '.js');
    if (typeof global[factoryName] !== 'function') {
      throw new Error(factoryName + ' not found after loading ' + name + '.js');
    }
    // extraConfig 可用于覆盖 Module 的 print / printErr 等（可选）
    const config = Object.assign(
      { locateFile: function (p) { return WASM_BASE + p; } },
      extraConfig || {}
    );
    const inst = await global[factoryName](config);
    _instances[key] = inst;
    return inst;
  }

  global.WasmLoader = {
    BASE: WASM_BASE,
    loadScript: loadScript,
    loadWasmModule: loadWasmModule,
    clearCache: function () {
      Object.keys(_instances).forEach(function (k) { delete _instances[k]; });
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
