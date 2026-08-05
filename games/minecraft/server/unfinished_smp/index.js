// 1. CONFIGURE YOUR SERVERS HERE
const SERVERS = [
  { name: "Unfinished SMP", ip: "unfinishedsmp.com" },
];

const container = document.getElementById("server-list");

// Fallback image if a server doesn't have an icon set
const DEFAULT_ICON = "https://api.mcsrvstat.us/icon/default";

function renderServerPanels() {
  container.innerHTML = "";

  SERVERS.forEach((server, index) => {
    const card = document.createElement("div");
    card.className = "mc-panel";

    card.innerHTML = `
      <div class="panel-left">
        <img id="icon-${index}" class="server-icon" src="${DEFAULT_ICON}" alt="Server Icon" />
        <div id="dot-${index}" class="status-dot"></div>
        <div class="mc-details">
          <div class="server-header">
            <span class="server-title">${server.name}</span>
            <span id="version-${index}" class="version-badge"></span>
          </div>
          <span id="count-${index}" class="player-count">Checking status...</span>
          <div id="motd-${index}" class="server-motd"></div>
          <div id="players-${index}" class="player-list"></div>
        </div>
      </div>
      <button class="copy-btn" onclick="copyServerIp('${server.ip}', this)">
        <span class="ip-text">${server.ip}</span>
        <span class="copy-badge">Copy</span>
      </button>
    `;

    container.appendChild(card);
  });
}

async function updateAllServers() {
  SERVERS.forEach(async (server, index) => {
    const iconEl = document.getElementById(`icon-${index}`);
    const dot = document.getElementById(`dot-${index}`);
    const versionEl = document.getElementById(`version-${index}`);
    const countEl = document.getElementById(`count-${index}`);
    const motdEl = document.getElementById(`motd-${index}`);
    const playersEl = document.getElementById(`players-${index}`);

    try {
      const response = await fetch(`https://api.mcsrvstat.us/3/${server.ip}?t=${Date.now()}`);
      const data = await response.json();

      if (data.online) {
        dot.className = "status-dot online";
        countEl.textContent = `${data.players.online} / ${data.players.max} Players Online`;

        // 1. Server Icon (Base64 data or direct icon URL)
        if (data.icon) {
          iconEl.src = data.icon;
        } else {
          iconEl.src = `https://api.mcsrvstat.us/icon/${server.ip}`;
        }

        // 2. Server Version & Software (e.g. 1.21.1 • Fabric)
        const versionText = data.version || "";
        const softwareText = data.software ? ` • ${data.software}` : "";
        
        if (versionText || softwareText) {
          versionEl.textContent = `${versionText}${softwareText}`;
          versionEl.style.display = "inline-block";
        }

        // 3. MOTD
        if (data.motd && data.motd.html) {
          motdEl.innerHTML = data.motd.html.join("<br>");
        } else if (data.motd && data.motd.clean) {
          motdEl.textContent = data.motd.clean.join(" ");
        }

        playersEl.innerHTML = ""; // Clear existing heads

        if (data.players.list && data.players.list.length > 0) {
          data.players.list.forEach(player => {
            // Extracts player name (handles string or object formats)
            const playerName = typeof player === "object" ? player.name : player;

            const img = document.createElement("img");
            img.className = "player-head";
            img.src = `https://mc-heads.net/avatar/${playerName}/24`;
            img.alt = playerName;
            img.title = playerName; // Browser tooltip on mouse hover

            playersEl.appendChild(img);
          });
        }

      } else {
        dot.className = "status-dot offline";
        countEl.textContent = "Server Offline";
        versionEl.style.display = "none";
        motdEl.textContent = "";
      }
    } catch (error) {
      console.error(`Error fetching status for ${server.ip}:`, error);
      dot.className = "status-dot offline";
      countEl.textContent = "Error fetching status";
      versionEl.style.display = "none";
      motdEl.textContent = "";
    }
  });
}

async function copyServerIp(ip, buttonEl) {
  try {
    await navigator.clipboard.writeText(ip);
    const badge = buttonEl.querySelector(".copy-badge");

    badge.textContent = "Copied!";
    badge.classList.add("copied");

    setTimeout(() => {
      badge.textContent = "Copy";
      badge.classList.remove("copied");
    }, 2000);
  } catch (err) {
    console.error("Failed to copy IP:", err);
  }
}

renderServerPanels();
updateAllServers();
setInterval(updateAllServers, 10000);