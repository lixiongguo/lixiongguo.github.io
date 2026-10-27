const os = require("os");
const { execFile } = require("child_process");

function parseCpuTime(text) {
  const parts = String(text).trim().split(":");
  if (parts.length === 3) {
    return Number(parts[0]) * 3600 + Number(parts[1]) * 60 + Number(parts[2]);
  }
  if (parts.length === 2) {
    return Number(parts[0]) * 60 + Number(parts[1]);
  }
  const value = Number(text);
  return Number.isFinite(value) ? value : 0;
}

function cpuSnapshot() {
  return os.cpus().map((cpu) => {
    let total = 0;
    for (const value of Object.values(cpu.times)) total += value;
    return { idle: cpu.times.idle, total };
  });
}

function macMemoryUsed() {
  return new Promise((resolve) => {
    execFile("vm_stat", (err, stdout) => {
      if (err || !stdout) {
        resolve(null);
        return;
      }
      const page = stdout.match(/page size of (\d+) bytes/);
      const pageSize = page ? Number(page[1]) : 16384;
      const pages = (name) => {
        const match = stdout.match(new RegExp(name + ":\\s+(\\d+)"));
        return match ? Number(match[1]) : 0;
      };
      const available = (pages("Pages free") + pages("Pages inactive") + pages("Pages speculative")) * pageSize;
      const total = os.totalmem();
      resolve(Math.max(0, total - available));
    });
  });
}

function queryProcesses(pids) {
  if (!pids.length) return Promise.resolve(new Map());
  return new Promise((resolve) => {
    execFile("ps", ["-p", pids.join(","), "-o", "pid=,cputime=,rss="], (err, stdout) => {
      const found = new Map();
      if (err && !stdout) {
        resolve(found);
        return;
      }
      for (const line of stdout.split("\n")) {
        const match = line.trim().match(/^(\d+)\s+(\S+)\s+(\d+)/);
        if (!match) continue;
        found.set(Number(match[1]), {
          cpuSeconds: parseCpuTime(match[2]),
          rssKB: Number(match[3])
        });
      }
      resolve(found);
    });
  });
}

function createProfiler(options) {
  const getAppMetrics = options.getAppMetrics;
  const getTools = options.getTools;
  const memTotal = os.totalmem();
  let lastCpu = null;
  const lastProcCpu = new Map();
  let timer = null;

  function percentSince(pid, cpuSeconds, now) {
    const previous = lastProcCpu.get(pid);
    lastProcCpu.set(pid, { cpuSeconds, at: now });
    if (!previous) return 0;
    const wall = (now - previous.at) / 1000;
    if (wall <= 0) return 0;
    return Math.max(0, ((cpuSeconds - previous.cpuSeconds) / wall) * 100);
  }

  async function sample() {
    const now = Date.now();
    const cpu = cpuSnapshot();
    const coreCpu = cpu.map((core, index) => {
      const previous = lastCpu && lastCpu[index];
      if (!previous) return 0;
      const totalDelta = core.total - previous.total;
      const idleDelta = core.idle - previous.idle;
      if (totalDelta <= 0) return 0;
      return Math.max(0, Math.min(1, 1 - idleDelta / totalDelta));
    });
    lastCpu = cpu;
    const sysCpu = coreCpu.reduce((sum, load) => sum + load, 0) / (coreCpu.length || 1);

    let appCpu = 0;
    let appRssKB = 0;
    try {
      for (const metric of getAppMetrics()) {
        appCpu += metric.cpu.percentCPUUsage || 0;
        appRssKB += metric.memory.workingSetSize || 0;
      }
    } catch (err) {
      appCpu = 0;
      appRssKB = 0;
    }

    const tools = getTools().filter((tool) => tool.pid);
    const [stats, macUsed] = await Promise.all([
      queryProcesses(tools.map((tool) => tool.pid)),
      process.platform === "darwin" ? macMemoryUsed() : Promise.resolve(null)
    ]);
    const memUsed = macUsed == null ? memTotal - os.freemem() : macUsed;
    const toolSamples = tools.map((tool) => {
      const stat = stats.get(tool.pid);
      if (!stat) {
        return { id: tool.id, title: tool.title, cpu: 0, rssMB: 0, alive: false };
      }
      return {
        id: tool.id,
        title: tool.title,
        cpu: percentSince(tool.pid, stat.cpuSeconds, now),
        rssMB: stat.rssKB / 1024,
        alive: true
      };
    });
    for (const pid of Array.from(lastProcCpu.keys())) {
      if (!tools.some((tool) => tool.pid === pid)) lastProcCpu.delete(pid);
    }

    return {
      at: now,
      coreCpu,
      sysCpu,
      memUsedGB: memUsed / (1024 * 1024 * 1024),
      memTotalGB: memTotal / (1024 * 1024 * 1024),
      appCpu,
      appRssMB: appRssKB / 1024,
      tools: toolSamples
    };
  }

  function start(onSample) {
    if (timer) return;
    const tick = () => {
      sample().then(onSample).catch(() => {});
    };
    tick();
    timer = setInterval(tick, 1000);
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
  }

  return { sample, start, stop, parseCpuTime };
}

module.exports = { createProfiler, parseCpuTime };
