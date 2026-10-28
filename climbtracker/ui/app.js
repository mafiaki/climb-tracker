"use strict";

const TIERS = ["Sin clasificar", "Bronce I", "Bronce II", "Bronce III", "Plata I", "Plata II", "Plata III",
  "Oro I", "Oro II", "Oro III", "Platino I", "Platino II", "Platino III", "Diamante I", "Diamante II",
  "Diamante III", "Campeón I", "Campeón II", "Campeón III", "Gran Campeón I", "Gran Campeón II",
  "Gran Campeón III", "Leyenda Supersónica"];
const TIERS_SHORT = TIERS.map(t => t.replace("Gran Campeón", "GC").replace("Leyenda Supersónica", "SSL"));
const ROMAN = ["I", "II", "III", "IV"];
const TIER_COLORS = ["#7d8899", "#c07a45", "#a9b5c3", "#e6b84a", "#5fd0e3", "#4d8ff5", "#b072f2", "#ee4a56", "#f2f4f8"];
const SSL = 22;
const HINTS = {
  steam: "Nombre de la URL de tu perfil, ID de 17 dígitos o enlace de Steam.",
  epic: "Nombre visible de la cuenta de Epic.",
  psn: "ID online de PlayStation.",
  xbl: "Gamertag de Xbox.",
  switch: "Nombre de Nintendo Switch.",
};

// Logos de plataforma (Simple Icons, CC0), incrustados para no depender de internet.
const PLATFORM_ICONS = {
  steam: { label: "Steam", color: "#66c0f4", d: "M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.495 2.028-4.524 4.524-4.524 2.494 0 4.524 2.031 4.524 4.527s-2.03 4.525-4.524 4.525h-.105l-4.076 2.911c0 .052.004.105.004.159 0 1.875-1.515 3.396-3.39 3.396-1.635 0-3.016-1.173-3.331-2.727L.436 15.27C1.862 20.307 6.486 24 11.979 24c6.627 0 11.999-5.373 11.999-12S18.605 0 11.979 0zM7.54 18.21l-1.473-.61c.262.543.714.999 1.314 1.25 1.297.539 2.793-.076 3.332-1.375.263-.63.264-1.319.005-1.949s-.75-1.121-1.377-1.383c-.624-.26-1.29-.249-1.878-.03l1.523.63c.956.4 1.409 1.5 1.009 2.455-.397.957-1.497 1.41-2.454 1.012H7.54zm11.415-9.303c0-1.662-1.353-3.015-3.015-3.015-1.665 0-3.015 1.353-3.015 3.015 0 1.665 1.35 3.015 3.015 3.015 1.663 0 3.015-1.35 3.015-3.015zm-5.273-.005c0-1.252 1.013-2.266 2.265-2.266 1.249 0 2.266 1.014 2.266 2.266 0 1.251-1.017 2.265-2.266 2.265-1.253 0-2.265-1.014-2.265-2.265z" },
  epic: { label: "Epic Games", color: "#e8e8e8", d: "M3.537 0C2.165 0 1.66.506 1.66 1.879V18.44a4.262 4.262 0 00.02.433c.031.3.037.59.316.92.027.033.311.245.311.245.153.075.258.13.43.2l8.335 3.491c.433.199.614.276.928.27h.002c.314.006.495-.071.928-.27l8.335-3.492c.172-.07.277-.124.43-.2 0 0 .284-.211.311-.243.28-.33.285-.621.316-.92a4.261 4.261 0 00.02-.434V1.879c0-1.373-.506-1.88-1.878-1.88zm13.366 3.11h.68c1.138 0 1.688.553 1.688 1.696v1.88h-1.374v-1.8c0-.369-.17-.54-.523-.54h-.235c-.367 0-.537.17-.537.539v5.81c0 .369.17.54.537.54h.262c.353 0 .523-.171.523-.54V8.619h1.373v2.143c0 1.144-.562 1.71-1.7 1.71h-.694c-1.138 0-1.7-.566-1.7-1.71V4.82c0-1.144.562-1.709 1.7-1.709zm-12.186.08h3.114v1.274H6.117v2.603h1.648v1.275H6.117v2.774h1.74v1.275h-3.14zm3.816 0h2.198c1.138 0 1.7.564 1.7 1.708v2.445c0 1.144-.562 1.71-1.7 1.71h-.799v3.338h-1.4zm4.53 0h1.4v9.201h-1.4zm-3.13 1.235v3.392h.575c.354 0 .523-.171.523-.54V4.965c0-.368-.17-.54-.523-.54zm-3.74 10.147a1.708 1.708 0 01.591.108 1.745 1.745 0 01.49.299l-.452.546a1.247 1.247 0 00-.308-.195.91.91 0 00-.363-.068.658.658 0 00-.28.06.703.703 0 00-.224.163.783.783 0 00-.151.243.799.799 0 00-.056.299v.008a.852.852 0 00.056.31.7.7 0 00.157.245.736.736 0 00.238.16.774.774 0 00.303.058.79.79 0 00.445-.116v-.339h-.548v-.565H7.37v1.255a2.019 2.019 0 01-.524.307 1.789 1.789 0 01-.683.123 1.642 1.642 0 01-.602-.107 1.46 1.46 0 01-.478-.3 1.371 1.371 0 01-.318-.455 1.438 1.438 0 01-.115-.58v-.008a1.426 1.426 0 01.113-.57 1.449 1.449 0 01.312-.46 1.418 1.418 0 01.474-.309 1.58 1.58 0 01.598-.111 1.708 1.708 0 01.045 0zm11.963.008a2.006 2.006 0 01.612.094 1.61 1.61 0 01.507.277l-.386.546a1.562 1.562 0 00-.39-.205 1.178 1.178 0 00-.388-.07.347.347 0 00-.208.052.154.154 0 00-.07.127v.008a.158.158 0 00.022.084.198.198 0 00.076.066.831.831 0 00.147.06c.062.02.14.04.236.061a3.389 3.389 0 01.43.122 1.292 1.292 0 01.328.17.678.678 0 01.207.24.739.739 0 01.071.337v.008a.865.865 0 01-.081.382.82.82 0 01-.229.285 1.032 1.032 0 01-.353.18 1.606 1.606 0 01-.46.061 2.16 2.16 0 01-.71-.116 1.718 1.718 0 01-.593-.346l.43-.514c.277.223.578.335.9.335a.457.457 0 00.236-.05.157.157 0 00.082-.142v-.008a.15.15 0 00-.02-.077.204.204 0 00-.073-.066.753.753 0 00-.143-.062 2.45 2.45 0 00-.233-.062 5.036 5.036 0 01-.413-.113 1.26 1.26 0 01-.331-.16.72.72 0 01-.222-.243.73.73 0 01-.082-.36v-.008a.863.863 0 01.074-.359.794.794 0 01.214-.283 1.007 1.007 0 01.34-.185 1.423 1.423 0 01.448-.066 2.006 2.006 0 01.025 0zm-9.358.025h.742l1.183 2.81h-.825l-.203-.499H8.623l-.198.498h-.81zm2.197.02h.814l.663 1.08.663-1.08h.814v2.79h-.766v-1.602l-.711 1.091h-.016l-.707-1.083v1.593h-.754zm3.469 0h2.235v.658h-1.473v.422h1.334v.61h-1.334v.442h1.493v.658h-2.255zm-5.3.897l-.315.793h.624zm-1.145 5.19h8.014l-4.09 1.348z" },
  psn: { label: "PlayStation", color: "#4d8ff5", d: "M8.984 2.596v17.547l3.915 1.261V6.688c0-.69.304-1.151.794-.991.636.18.76.814.76 1.505v5.875c2.441 1.193 4.362-.002 4.362-3.152 0-3.237-1.126-4.675-4.438-5.827-1.307-.448-3.728-1.186-5.39-1.502zm4.656 16.241l6.296-2.275c.715-.258.826-.625.246-.818-.586-.192-1.637-.139-2.357.123l-4.205 1.5V14.98l.24-.085s1.201-.42 2.913-.615c1.696-.18 3.785.03 5.437.661 1.848.601 2.04 1.472 1.576 2.072-.465.6-1.622 1.036-1.622 1.036l-8.544 3.107V18.86zM1.807 18.6c-1.9-.545-2.214-1.668-1.352-2.32.801-.586 2.16-1.052 2.16-1.052l5.615-2.013v2.313L4.205 17c-.705.271-.825.632-.239.826.586.195 1.637.15 2.343-.12L8.247 17v2.074c-.12.03-.256.044-.39.073-1.939.331-3.996.196-6.038-.479z" },
  xbl: { label: "Xbox", color: "#3fbf3f", d: "M4.102 21.033C6.211 22.881 8.977 24 12 24c3.026 0 5.789-1.119 7.902-2.967 1.877-1.912-4.316-8.709-7.902-11.417-3.582 2.708-9.779 9.505-7.898 11.417zm11.16-14.406c2.5 2.961 7.484 10.313 6.076 12.912C23.002 17.48 24 14.861 24 12.004c0-3.34-1.365-6.362-3.57-8.536 0 0-.027-.022-.082-.042-.063-.022-.152-.045-.281-.045-.592 0-1.985.434-4.805 3.246zM3.654 3.426c-.057.02-.082.041-.086.042C1.365 5.642 0 8.664 0 12.004c0 2.854.998 5.473 2.661 7.533-1.401-2.605 3.579-9.951 6.08-12.91-2.82-2.813-4.216-3.245-4.806-3.245-.131 0-.223.021-.281.046v-.002zM12 3.551S9.055 1.828 6.755 1.746c-.903-.033-1.454.295-1.521.339C7.379.646 9.659 0 11.984 0H12c2.334 0 4.605.646 6.766 2.085-.068-.046-.615-.372-1.52-.339C14.946 1.828 12 3.545 12 3.545v.006z" },
  switch: { label: "Nintendo Switch", color: "#ff4d55", d: "M14.176 24h3.674c3.376 0 6.15-2.774 6.15-6.15V6.15C24 2.775 21.226 0 17.85 0H14.1c-.074 0-.15.074-.15.15v23.7c-.001.076.075.15.226.15zm4.574-13.199c1.351 0 2.399 1.125 2.399 2.398 0 1.352-1.125 2.4-2.399 2.4-1.35 0-2.4-1.049-2.4-2.4-.075-1.349 1.05-2.398 2.4-2.398zM11.4 0H6.15C2.775 0 0 2.775 0 6.15v11.7C0 21.226 2.775 24 6.15 24h5.25c.074 0 .15-.074.15-.149V.15c.001-.076-.075-.15-.15-.15zM9.676 22.051H6.15c-2.326 0-4.201-1.875-4.201-4.201V6.15c0-2.326 1.875-4.201 4.201-4.201H9.6l.076 20.102zM3.75 7.199c0 1.275.975 2.25 2.25 2.25s2.25-.975 2.25-2.25c0-1.273-.975-2.25-2.25-2.25s-2.25.977-2.25 2.25z" },
};

const S = { config: {}, players: [], playlists: [], platforms: [], thresholds: {}, open: new Set(), live: {}, liveMsg: "" };
const api = () => window.pywebview.api;
const $ = (sel, root = document) => root.querySelector(sel);
const list = $("#list");

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const tierColor = t => TIER_COLORS[t ? Math.min(Math.ceil(t / 3), 8) : 0];
const rankIcon = t => `https://trackercdn.com/cdn/tracker.gg/rocket-league/ranks/s4-${t}.png`;
const signed = n => (n > 0 ? "+" : n < 0 ? "−" : "±") + Math.abs(n);
const sameDay = (a, b) => a.toDateString() === b.toDateString();

function platIcon(platform) {
  const p = PLATFORM_ICONS[platform];
  if (!p) return "";
  return `<svg class="plat" viewBox="0 0 24 24" style="color:${p.color}" role="img" aria-label="${p.label}"><title>${p.label}</title><path d="${p.d}"/></svg>`;
}

function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "ahora";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return `hace ${Math.floor(s / 86400)} d`;
}

function when(iso) {
  const d = new Date(iso), now = new Date();
  const hm = d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  if (sameDay(d, now)) return `hoy ${hm}`;
  if (sameDay(d, new Date(now.getTime() - 86400000))) return `ayer ${hm}`;
  return `${d.toLocaleDateString("es-ES", { day: "numeric", month: "short" })} ${hm}`;
}

// ---------- cálculos ----------

/** Lo que falta para subir/bajar de división y para el siguiente rango. */
function progress(pl, rows) {
  const r = { up: pl.deltaUp, down: pl.deltaDown, upLabel: null, nextRank: null, pct: null };
  if (!pl.tier || pl.mmr == null) return r;
  const find = (t, d) => rows && rows.find(x => x.tier === t && x.division === d);
  if (pl.tier < SSL) {
    const lastDiv = pl.division >= 3;
    r.upLabel = lastDiv ? TIERS_SHORT[pl.tier + 1] : `Div ${ROMAN[pl.division + 1]}`;
    const nextDiv = lastDiv ? find(pl.tier + 1, 0) : find(pl.tier, pl.division + 1);
    if (r.up == null && nextDiv) r.up = Math.max(0, nextDiv.min - pl.mmr);
    const nextTier = find(pl.tier + 1, 0);
    if (!lastDiv && nextTier) r.nextRank = Math.max(0, nextTier.min - pl.mmr);
  } else {
    r.up = null;
  }
  const cur = find(pl.tier, pl.division);
  if (r.down == null && cur) r.down = Math.max(0, pl.mmr - cur.min);
  // divPct: avance dentro de la división. pct: avance dentro del rango entero, con
  // las 4 divisiones como 4 tramos iguales (la barra los dibuja separados).
  if (r.up != null && r.down != null && r.up + r.down > 0) r.divPct = r.down / (r.up + r.down);
  if (pl.tier >= SSL) r.pct = 1;
  else if (r.divPct != null) r.pct = (Math.min(pl.division, 3) + r.divPct) / 4;
  return r;
}

/** Barra del rango: 4 tramos (Div I–IV), rellena hasta donde está el jugador. */
function barHTML(pl, pr) {
  const pctTxt = Math.round(pr.pct * 100);
  const title = pl.tier >= SSL ? "Leyenda Supersónica"
    : `${TIERS[pl.tier]}: ${pctTxt}% del rango · Div ${ROMAN[pl.division]}: ${pr.down} de ${pr.up + pr.down} MMR`;
  const ticks = pl.tier >= SSL ? "" : `<b style="left:25%"></b><b style="left:50%"></b><b style="left:75%"></b>`;
  return `<div class="bar" title="${esc(title)}"><i style="width:${pctTxt}%"></i>${ticks}</div>`;
}

/** Partidas recientes de una lista. Tracker a veces agrupa varias en una entrada. */
const recent = (p, pid) => (p.sessions || []).filter(e => e.pl === pid && (e.n > 0 || e.d));

function outcome(e) {
  if (e.n >= 2) return { w: e.w, l: Math.max(0, e.n - e.w) };
  // El campo victoria/derrota de Tracker a veces no cuadra; el cambio de MMR es más fiable.
  if (e.d > 0) return { w: 1, l: 0 };
  if (e.d < 0) return { w: 0, l: 1 };
  return e.n === 1 ? { w: e.w ? 1 : 0, l: e.w ? 0 : 1 } : { w: 0, l: 0 };
}

/** Victorias, derrotas y MMR neto de las partidas que cumplen `keep`. */
function tally(entries, keep) {
  let w = 0, l = 0, net = 0, any = false;
  for (const e of entries) {
    if (!keep(e)) continue;
    const o = outcome(e);
    w += o.w; l += o.l; net += e.d || 0; any = true;
  }
  return any ? { w, l, net } : null;
}

const isToday = e => sameDay(new Date(e.t), new Date());
const inSession = e => !!S.config.session_start && new Date(e.t) >= new Date(S.config.session_start);

function resultHTML(label, r, title) {
  const cls = r.net > 0 ? "pos" : r.net < 0 ? "neg" : "";
  return `<span title="${esc(title)}">${label} <b class="${cls}">${signed(r.net)}</b> ${r.w}V ${r.l}D</span>`;
}

// ---------- pintado ----------

function render() {
  document.body.classList.toggle("compact", !!S.config.compact);
  $("#btn-pin").classList.toggle("on", !!S.config.on_top);
  $("#btn-session").title = S.config.session_start
    ? `Nueva sesión · la actual empezó ${when(S.config.session_start)}` : "Nueva sesión";
  renderTabs();
  renderLive();
  if (!S.players.length) {
    list.innerHTML = `<div class="empty"><b>Sin jugadores</b>Pulsa + para añadir a quien quieras seguir.</div>`;
    return;
  }
  list.innerHTML = S.players.map(cardHTML).join("");
  updateRefreshIcon();
}

function renderTabs() {
  $("#tabs").innerHTML = S.playlists.map(pl =>
    `<button class="tab${pl.id === S.config.playlist ? " active" : ""}" data-pl="${pl.id}" title="${esc(pl.name)}">${esc(pl.short)}</button>`
  ).join("");
  const active = $("#tabs .active");
  if (active) active.scrollIntoView({ block: "nearest", inline: "nearest" });
}

function updateCard(key) {
  if (drag) return;  // se repinta todo al soltar
  const p = S.players.find(x => x.key === key);
  const el = list.querySelector(`.card[data-key="${CSS.escape(key)}"]`);
  if (p && el) el.outerHTML = cardHTML(p);
  updateRefreshIcon();
}

function updateRefreshIcon() {
  const live = (S.live.match && S.live.match.players) || [];
  $("#btn-refresh").classList.toggle("spin", S.players.some(p => p.loading) || live.some(p => p.loading));
}

/** Partida recién acabada (Stats API): su resultado mientras llega el MMR nuevo de Tracker. */
function postHTML(post) {
  const res = post.won == null ? "Partida terminada"
    : `<span class="pill ${post.won ? "win" : "loss"}">${post.won ? "Victoria" : "Derrota"}</span>`;
  return `<div class="post-line">${res}<span>actualizando MMR…</span></div>`;
}

/** Tarjeta de jugador. Con opt.live es la tarjeta compacta de la sección "En partida". */
function cardHTML(p, opt = {}) {
  const live = !!opt.live;
  const pid = live ? opt.pid : S.config.playlist;
  const prof = p.profile;
  const pl = prof && prof.playlists[String(pid)];
  const open = !live && S.open.has(p.key);
  const busy = p.loading ? `<span class="busy" title="Actualizando"></span>` : "";
  const err = p.error ? `<div class="error-line">${esc(p.error.message)}${p.error.kind === "notfound" ? "" : " · reintentando"}</div>` : "";
  const cls = `card${open ? " open" : ""}${live ? " mini" : ""}`;
  const extra = live ? liveAction(p) : "";
  const post = p.post ? postHTML(p.post) : "";
  // La barra de color de la izquierda sirve de asa para reordenar (solo en la lista fija).
  const grip = live ? "" : `<div class="grip" title="Arrastra para reordenar"></div>`;

  if (!pl) {
    const msg = p.kind === "bot" ? "Bot" : p.kind === "guest" ? "Invitado (pantalla dividida)"
      : prof ? "Sin datos en esta lista" : p.error ? "" : live ? "Buscando en Tracker…" : "Cargando…";
    return `<div class="${cls}" data-key="${esc(p.key)}">${grip}
      <div class="row1"><div class="rank none"></div>
        <div class="who"><div class="name">${platIcon(p.platform)}<span>${esc(p.name)}</span>${busy}</div><div class="nodata">${msg}</div></div>${extra}
      </div>${post}${err}${open ? detailsHTML(p, null) : ""}</div>`;
  }

  const ranked = pl.tier > 0;
  const pr = progress(pl, S.thresholds[pid]);
  const est = pl.estimated ? ` <span class="est" title="Rango estimado por Tracker">~</span>` : "";
  const tierText = ranked
    ? `${TIERS[pl.tier]}${pl.tier < SSL ? ` <span class="div">· Div ${ROMAN[pl.division]}</span>` : ""}${est}`
    : "Sin clasificar";
  const icon = pl.icon || rankIcon(pl.tier);

  const line1 = [];
  if (ranked && pr.up != null && pr.upLabel)
    line1.push(`<span class="up" title="MMR que falta para subir">▲ <b>${pr.up}</b> ${esc(pr.upLabel)}</span>`);
  if (ranked && pr.down != null)
    line1.push(`<span class="down" title="MMR que puedes perder antes de bajar de división">▼ <b>${pr.down}</b></span>`);
  if (ranked && pr.nextRank != null)
    line1.push(`<span title="MMR que falta para el siguiente rango"><b>${pr.nextRank}</b> para ${esc(TIERS_SHORT[pl.tier + 1])}</span>`);

  const line2 = [`<span title="Partidas jugadas esta temporada"><b>${pl.matches}</b> partidas</span>`];
  if (pl.streak > 0) {
    const win = pl.streakType === "win";
    line2.push(`<span class="pill ${win ? "win" : "loss"}" title="Racha actual">Racha ${pl.streak}&nbsp;${win ? "V" : "D"}</span>`);
  }
  const ents = recent(p, pid), mode = S.config.result_mode || "both";
  const results = [];
  const day = mode !== "session" && tally(ents, isToday);
  if (day) results.push(resultHTML("Hoy", day, "MMR ganado o perdido hoy"));
  const sess = mode !== "day" && tally(ents, inSession);
  if (sess) results.push(resultHTML("Sesión", sess, `MMR ganado o perdido desde ${when(S.config.session_start)}`));

  return `<div class="${cls}" data-key="${esc(p.key)}" style="--tier:${tierColor(pl.tier)}">${grip}
    <div class="row1">
      <img class="rank" src="${esc(icon)}" alt="">
      <div class="who">
        <div class="name">${platIcon(p.platform)}<span>${esc(p.name)}</span>${busy}</div>
        <div class="tier">${tierText}</div>
      </div>${extra}
      <div class="mmr"><b>${pl.mmr ?? "—"}</b><small class="lbl">MMR</small>${ranked && pr.up != null && pr.upLabel ? `<small class="cup" title="MMR que falta para subir a ${esc(pr.upLabel)}">▲${pr.up}</small>` : ""}</div>
    </div>
    ${post}
    ${ranked && pr.pct != null ? barHTML(pl, pr) : ""}
    ${line1.length ? `<div class="stats">${line1.join("")}</div>` : ""}
    <div class="stats" style="margin-top:3px">${line2.join("")}</div>
    ${results.length ? `<div class="stats results">${results.join("")}</div>` : ""}
    ${err}
    ${open ? detailsHTML(p, pl) : ""}
  </div>`;
}

// El alto del viewBox coincide con el alto en píxeles (CSS), así las posiciones sirven tal cual.
const SPARK_W = 300, SPARK_H = 72, SPARK_P = 5;

/**
 * Puntos de la gráfica (de la partida más vieja a la más nueva) y las líneas de
 * división/rango que caen dentro. El eje se amplía hasta la división de justo
 * debajo y la de justo encima de los datos, para ver siempre entre qué líneas se está.
 */
function sparkPoints(entries, rows) {
  const ents = entries.slice(0, 30).filter(e => e.mmr != null).reverse();
  if (ents.length < 2) return null;
  const vals = ents.map(e => e.mmr);
  const dataLo = Math.min(...vals), dataHi = Math.max(...vals);
  const bounds = (rows || []).filter(r => r.tier > 0 && r.min != null)
    .map(r => ({ v: r.min, tier: r.tier, division: r.division }))
    .sort((a, b) => a.v - b.v);
  const below = bounds.filter(b => b.v <= dataLo).pop();
  const above = bounds.find(b => b.v > dataHi);
  const lo = below ? below.v : dataLo, hi = above ? above.v : dataHi, span = hi - lo || 1;
  const yOf = v => SPARK_P + (1 - (v - lo) / span) * (SPARK_H - 2 * SPARK_P);
  const pts = ents.map((e, i) => ({ e, x: (i / (ents.length - 1)) * SPARK_W, y: yOf(e.mmr) }));
  const lines = bounds.filter(b => b.v >= lo && b.v <= hi).map(b => ({ ...b, y: yOf(b.v) }));
  return { pts, lines, lo: dataLo, hi: dataHi };
}

/**
 * Líneas horizontales de división (discontinuas) y de rango (del color del rango).
 * Cada línea cruza la gráfica y acaba en su etiqueta, a la misma altura, en una
 * franja a la derecha. Si dos etiquetas no caben, se acercan un poco o se omite
 * la menos importante: mandan las de rango y luego las más cercanas al MMR actual.
 */
function sparkLinesHTML(lines, cur, curTier) {
  const LH = 12, NUDGE = 3;
  const placed = [];
  const order = [...lines].sort((a, b) =>
    (a.division === 0 ? 0 : 1) - (b.division === 0 ? 0 : 1) || Math.abs(a.v - cur) - Math.abs(b.v - cur));
  for (const l of order) {
    const fits = c => c - LH / 2 >= -2 && c + LH / 2 <= SPARK_H + 2 && placed.every(p => Math.abs(p.c - c) >= LH);
    const c = [0, -NUDGE, NUDGE].map(d => l.y + d).find(fits);
    if (c != null) placed.push({ l, c });
  }
  const rules = lines.map(l => {
    const tier = l.division === 0;
    return `<div class="spark-line${tier ? " tier" : ""}" style="top:${l.y.toFixed(1)}px${tier ? `;--lc:${tierColor(l.tier)}` : ""}"></div>`;
  });
  const labels = placed.map(({ l, c }) => {
    const tier = l.division === 0;
    const name = tier ? TIERS[l.tier] : `${l.tier !== curTier ? `${TIERS[l.tier]} · ` : ""}Div ${ROMAN[l.division]}`;
    // Rango: su icono y el MMR. División: "Div II 1335" (con el icono si es de otro rango).
    const icon = tier || l.tier !== curTier ? `<img src="${esc(rankIcon(l.tier))}" alt="">` : "";
    const body = tier ? `${icon}<b>${l.v}</b>` : `${icon}Div ${ROMAN[l.division]} <b>${l.v}</b>`;
    return `<span class="spark-label${tier ? " tier" : ""}" style="top:${c.toFixed(1)}px${tier ? `;--lc:${tierColor(l.tier)}` : ""}" title="${esc(`${name}: desde ${l.v} MMR`)}">${body}</span>`;
  });
  return rules.join("") + labels.join("");
}

function sparkSVG(entries, curTier) {
  const sp = sparkPoints(entries, S.thresholds[S.config.playlist]);
  if (!sp) return "";
  const line = sp.pts.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join("");
  return `<div><div class="sec-title">MMR reciente · ${sp.lo}–${sp.hi}</div>
    <div class="spark-wrap">
      ${sparkLinesHTML(sp.lines, sp.pts[sp.pts.length - 1].e.mmr, curTier)}
      <svg class="spark" viewBox="0 0 ${SPARK_W} ${SPARK_H}" preserveAspectRatio="none">
        <path class="a" d="${line}L${SPARK_W},${SPARK_H}L0,${SPARK_H}Z"/>
        <path class="l" d="${line}" vector-effect="non-scaling-stroke"/>
      </svg>
      <i class="spark-x" hidden></i><i class="spark-dot" hidden></i>
      <div class="spark-tip" hidden></div>
    </div></div>`;
}

// Al pasar el ratón por la gráfica: MMR, cambio y fecha de la partida más cercana.
list.addEventListener("pointermove", e => {
  const wrap = !drag && e.target.closest(".spark-wrap");
  if (!wrap) return;
  const p = S.players.find(x => x.key === wrap.closest(".card").dataset.key);
  const sp = p && sparkPoints(recent(p, S.config.playlist), S.thresholds[S.config.playlist]);
  if (!sp) return;
  // La curva ocupa el SVG; a su derecha queda la franja de las etiquetas.
  const r = wrap.querySelector("svg").getBoundingClientRect();
  const ratio = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
  const pt = sp.pts[Math.round(ratio * (sp.pts.length - 1))];
  const x = (pt.x / SPARK_W) * r.width, y = (pt.y / SPARK_H) * r.height;
  const [line, dot, tip] = [wrap.querySelector(".spark-x"), wrap.querySelector(".spark-dot"), wrap.querySelector(".spark-tip")];
  line.style.left = `${x}px`;
  dot.style.left = `${x}px`;
  dot.style.top = `${y}px`;
  const d = pt.e.d;
  const games = pt.e.n >= 2 ? ` · ${pt.e.n} partidas` : "";
  tip.innerHTML = `<b>${pt.e.mmr}</b>${d == null ? "" : ` <span class="${d > 0 ? "pos" : d < 0 ? "neg" : ""}">${signed(d)}</span>`} · ${esc(when(pt.e.t))}${games}`;
  line.hidden = dot.hidden = tip.hidden = false;
  // El recuadro sigue al punto pero sin salirse de la gráfica.
  const half = tip.offsetWidth / 2;
  tip.style.left = `${Math.min(wrap.clientWidth - half, Math.max(half, x))}px`;
});

list.addEventListener("pointerout", e => {
  const wrap = e.target.closest(".spark-wrap");
  if (!wrap || wrap.contains(e.relatedTarget)) return;
  wrap.querySelectorAll(".spark-x, .spark-dot, .spark-tip").forEach(el => { el.hidden = true; });
});

function matchRow(e) {
  const o = outcome(e);
  let res;
  if (e.n >= 2) res = `<span class="res">${e.n} partidas · ${o.w}V ${o.l}D</span>`;
  else res = o.w ? `<span class="res pos">Victoria</span>` : o.l ? `<span class="res neg">Derrota</span>` : `<span class="res">—</span>`;
  const d = e.d ?? 0;
  return `<div class="match">
    <span class="when">${esc(when(e.t))}</span>${res}
    <span class="delta ${d > 0 ? "pos" : d < 0 ? "neg" : ""}">${e.d == null ? "" : signed(d)}</span>
    <span class="after">${e.mmr ?? ""}</span>
  </div>`;
}

function detailsHTML(p, pl) {
  const pid = S.config.playlist;
  const prof = p.profile || {};
  const ents = recent(p, pid);
  let h = `<div class="details">`;
  if (pl) {
    h += sparkSVG(ents, pl.tier);
    h += ents.length
      ? `<div><div class="sec-title">Últimas partidas</div><div class="matches">${ents.slice(0, 8).map(matchRow).join("")}</div></div>`
      : `<div class="nodata">Tracker no tiene partidas recientes de esta lista.</div>`;
  }
  const others = S.playlists.filter(x => x.id !== pid && x.id !== 0 && prof.playlists && prof.playlists[x.id]);
  if (others.length) {
    h += `<div><div class="sec-title">Otras listas</div><div class="others">${others.map(x => {
      const o = prof.playlists[x.id];
      return `<button class="other" data-pl="${x.id}" title="${esc(TIERS[o.tier] || "")}"><img src="${esc(o.icon || rankIcon(o.tier))}" alt="">${esc(x.short)} <b>${o.mmr ?? "—"}</b></button>`;
    }).join("")}</div></div>`;
  }
  const peak = prof.peaks && prof.peaks[String(pid)];
  h += `<div class="foot">
    <span class="grow">${prof.updated ? `Tracker: ${ago(prof.updated)}` : ""}${peak && peak.mmr ? ` · Pico ${peak.mmr}` : ""}</span>
    <button class="link" data-act="up" title="Subir en la lista">↑</button>
    <button class="link" data-act="down" title="Bajar en la lista">↓</button>
    <button class="link" data-act="web" title="Abrir en rocketleague.tracker.network">Tracker ↗</button>
    <button class="link danger" data-act="remove">Quitar</button>
  </div></div>`;
  return h;
}

// ---------- en partida (Stats API del juego) ----------

const PLUS = `<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>`;

const EXTERNAL = `<svg viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>`;

function liveAction(p) {
  if (p.kind !== "player") return "";
  const web = `<button class="icon web" data-live="web" title="Ver su perfil en Tracker">${EXTERNAL}</button>`;
  if (p.tracked) return `${web}<span class="tracked" title="Ya está en tu lista">✓</span>`;
  return `${web}<button class="icon add" data-live="add" title="Añadir a mi lista">${PLUS}</button>`;
}

function teamHTML(players, team, pid) {
  const ps = players.filter(p => p.team === team);
  if (!ps.length) return "";
  const mmrs = ps.map(p => p.profile && p.profile.playlists[String(pid)]).filter(pl => pl && pl.mmr != null).map(pl => pl.mmr);
  const avg = mmrs.length ? `<span title="MMR medio del equipo">media ${Math.round(mmrs.reduce((a, b) => a + b, 0) / mmrs.length)}</span>` : "";
  return `<div class="team t${team}">
    <div class="team-name">${team ? "Naranja" : "Azul"}${avg}</div>
    ${ps.map(p => cardHTML(p, { live: true, pid })).join("")}
  </div>`;
}

function renderLive() {
  const el = $("#live");
  const lv = S.live || {};
  const pos = S.config.match_pos || "off";
  const m = pos !== "off" && lv.match;
  // La sección va encima o debajo de la lista según Ajustes → Mostrar partida.
  if (pos === "top" ? el.nextElementSibling !== list : el.previousElementSibling !== list) {
    if (pos === "top") list.before(el); else list.after(el);
  }
  const parts = [];
  if (lv.ini_reset) {
    parts.push(`<div class="notice">Una actualización del juego apagó la Stats API.
      <button class="link" data-live="enable">Activar</button>
      <button class="link" data-live="forget" title="No volver a avisar">✕</button></div>`);
  }
  if (S.liveMsg) parts.push(`<div class="notice">${esc(S.liveMsg)}</div>`);
  if (m && m.players.length) {
    // Al acabar se queda plegada en una línea; un clic en la cabecera la abre.
    const folded = m.ended && !S.liveOpen;
    const pl = S.playlists.find(x => x.id === m.playlist);
    // Rango de la pestaña elegida (por defecto) o de la lista que se está jugando.
    const rankPid = S.config.match_rank === "match" && m.playlist != null ? m.playlist : S.config.playlist;
    const rankPl = rankPid !== m.playlist && S.playlists.find(x => x.id === rankPid);
    const won = m.ended && m.winner != null ? `<span class="pl">· ganó ${m.winner ? "naranja" : "azul"}</span>` : "";
    parts.push(`<div class="live-head${m.ended ? " fold" : ""}"${m.ended ? ` data-live="fold" title="${folded ? "Ver" : "Plegar"}"` : ""}>
      <span class="live-dot${m.ended ? " off" : ""}"></span>${m.ended ? "Última partida" : "En partida"}
      ${pl ? `<span class="pl" title="${esc(pl.name)}">· ${esc(pl.short)}</span>` : ""}${won}
      ${rankPl ? `<span class="pl" title="Rangos de ${esc(rankPl.name)} (cámbialo en Ajustes)">· rango ${esc(rankPl.short)}</span>` : ""}
      ${m.ended ? `<span class="chev">${folded ? "▸" : "▾"}</span>` : ""}
      <span class="grow"></span>
      <button class="link" data-live="dismiss" title="Ocultar hasta la próxima partida">✕</button>
    </div>`);
    if (!folded) parts.push(teamHTML(m.players, 0, rankPid) + teamHTML(m.players, 1, rankPid));
  }
  el.hidden = !parts.length;
  el.innerHTML = parts.join("");
}

function liveMessage(text) {
  S.liveMsg = text;
  renderLive();
  clearTimeout(liveMessage.t);
  liveMessage.t = setTimeout(() => { S.liveMsg = ""; renderLive(); }, 5000);
}

$("#live").addEventListener("click", async e => {
  const b = e.target.closest("[data-live]");
  if (!b) return;
  const a = b.dataset.live;
  if (a === "fold") { S.liveOpen = !S.liveOpen; renderLive(); }
  if (a === "dismiss") api().dismiss_live();
  if (a === "web") api().open_live_profile(b.closest(".card").dataset.key);
  if (a === "forget") api().dismiss_ini_reset();
  if (a === "enable") {
    const st = await api().enable_stats_api();
    liveMessage(st.error || "Hecho. Reinicia Rocket League para que se aplique.");
  }
  if (a === "add") {
    b.disabled = true;
    const res = await api().add_live_player(b.closest(".card").dataset.key);
    if (!res.ok) { b.disabled = false; return liveMessage(res.error); }
    S.players.push(res.player);
    render();
  }
});

// ---------- acciones ----------

const pendingThresholds = new Set();

async function ensureThresholds(pid) {
  if (pid == null || S.thresholds[pid] || pid === 0 || pendingThresholds.has(pid)) return;
  pendingThresholds.add(pid);
  try {
    const rows = await api().get_thresholds(pid);
    if (rows) {
      S.thresholds[pid] = rows;
      render();
    }
  } finally {
    pendingThresholds.delete(pid);
  }
}

function setPlaylist(pid) {
  if (pid === S.config.playlist) return;
  S.config.playlist = pid;
  api().set_option("playlist", pid);
  render();
  ensureThresholds(pid);
}

function setOption(name, value) {
  S.config[name] = value;
  api().set_option(name, value);
  render();
}

$("#tabs").addEventListener("click", e => {
  const b = e.target.closest(".tab");
  if (b) setPlaylist(Number(b.dataset.pl));
});
// La rueda del ratón desplaza las pestañas en horizontal.
$("#tabs").addEventListener("wheel", e => {
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
    e.currentTarget.scrollLeft += e.deltaY;
    e.preventDefault();
  }
}, { passive: false });

// ---------- reordenar arrastrando la barra de la izquierda ----------

let drag = null;
const scroller = $("main");
const midY = el => { const r = el.getBoundingClientRect(); return r.top + r.height / 2; };

list.addEventListener("pointerdown", e => {
  const grip = e.target.closest(".grip");
  if (!grip || e.button !== 0) return;
  e.preventDefault();
  const card = grip.closest(".card");
  const rect = card.getBoundingClientRect();
  try { grip.setPointerCapture(e.pointerId); } catch { /* sin captura también funciona dentro de la lista */ }
  drag = { card, key: card.dataset.key, startY: e.clientY, offset: e.clientY - rect.top, h: rect.height, moved: false };
});

list.addEventListener("pointermove", e => {
  if (!drag) return;
  if (!drag.moved) {
    if (Math.abs(e.clientY - drag.startY) < 4) return;
    drag.moved = true;
    drag.card.classList.add("dragging");
    document.body.classList.add("is-dragging");
  }
  const { card } = drag;
  // Cuando el centro de la tarjeta cruza la mitad de una vecina, cambian de sitio.
  const center = e.clientY - drag.offset + drag.h / 2;
  let prev = card.previousElementSibling, next = card.nextElementSibling;
  while (prev && center < midY(prev)) { list.insertBefore(card, prev); prev = card.previousElementSibling; }
  while (next && center > midY(next)) { list.insertBefore(card, next.nextElementSibling); next = card.nextElementSibling; }
  // La tarjeta sigue al ratón.
  card.style.transform = "";
  card.style.transform = `translateY(${e.clientY - drag.offset - card.getBoundingClientRect().top}px)`;
  // Si la lista no cabe, desplaza al acercarse a los bordes.
  const box = scroller.getBoundingClientRect();
  if (e.clientY < box.top + 28) scroller.scrollTop -= 10;
  else if (e.clientY > box.bottom - 28) scroller.scrollTop += 10;
});

function endDrag() {
  if (!drag) return;
  const { card, key, moved } = drag;
  drag = null;
  card.classList.remove("dragging");
  card.style.transform = "";
  document.body.classList.remove("is-dragging");
  if (moved) {
    const from = S.players.findIndex(p => p.key === key);
    const to = [...list.querySelectorAll(".card")].findIndex(c => c.dataset.key === key);
    if (from >= 0 && to >= 0 && to !== from) {
      S.players.splice(to, 0, S.players.splice(from, 1)[0]);
      api().move_player(key, to - from);
    }
  }
  render();  // aplica también lo que llegó mientras se arrastraba
}
list.addEventListener("pointerup", endDrag);
list.addEventListener("pointercancel", endDrag);

list.addEventListener("click", async e => {
  const card = e.target.closest(".card");
  if (!card || e.target.closest(".grip")) return;
  const key = card.dataset.key;
  const other = e.target.closest(".other");
  if (other) return setPlaylist(Number(other.dataset.pl));
  const act = e.target.closest("[data-act]");
  if (act) {
    const a = act.dataset.act;
    if (a === "web") api().open_profile(key);
    if (a === "remove") {
      // Primer clic pide confirmación, el segundo quita.
      if (!act.dataset.armed) {
        act.dataset.armed = "1";
        act.textContent = "¿Seguro?";
        setTimeout(() => { if (act.isConnected) { delete act.dataset.armed; act.textContent = "Quitar"; } }, 3000);
        return;
      }
      await api().remove_player(key);
      S.players = S.players.filter(x => x.key !== key);
      S.open.delete(key);
      render();
    }
    if (a === "up" || a === "down") {
      const i = S.players.findIndex(x => x.key === key);
      const j = i + (a === "up" ? -1 : 1);
      if (i < 0 || j < 0 || j >= S.players.length) return;
      S.players.splice(j, 0, S.players.splice(i, 1)[0]);
      api().move_player(key, a === "up" ? -1 : 1);
      render();
    }
    return;
  }
  if (card.classList.contains("open")) {
    // Con el detalle abierto, solo la cabecera de la tarjeta lo cierra.
    if (!e.target.closest(".row1")) return;
    S.open.delete(key);
  } else {
    S.open.add(key);
  }
  updateCard(key);
});

$("#btn-refresh").addEventListener("click", () => api().refresh_now());
$("#btn-session").addEventListener("click", () => {
  const prev = S.config.session_start;
  const now = new Date();
  setOption("session_start", now.toISOString());
  const hm = now.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  toast(`Nueva sesión desde las ${hm}`, "Deshacer", () => setOption("session_start", prev));
});

// Aviso breve abajo, con un botón opcional (p. ej. deshacer).
const toastEl = $("#toast");
function toast(text, actionLabel, onAction) {
  toastEl.innerHTML = `<span>${esc(text)}</span>${actionLabel ? `<button class="link">${esc(actionLabel)}</button>` : ""}`;
  toastEl.hidden = false;
  const btn = toastEl.querySelector("button");
  if (btn) btn.onclick = () => { onAction(); toastEl.hidden = true; };
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { toastEl.hidden = true; }, 6000);
}
$("#btn-pin").addEventListener("click", () => setOption("on_top", !S.config.on_top));
$("#btn-add").addEventListener("click", openAdd);
$("#btn-settings").addEventListener("click", openSettings);

// ---------- ventanas emergentes ----------

const modal = $("#modal"), sheet = $("#sheet");

function showModal(tplId) {
  sheet.replaceChildren($(tplId).content.cloneNode(true));
  modal.hidden = false;
}
function closeModal() { modal.hidden = true; sheet.replaceChildren(); setupState = null; }

modal.addEventListener("click", e => {
  if (e.target === modal || e.target.closest("[data-close]")) closeModal();
});
document.addEventListener("keydown", e => { if (e.key === "Escape" && !modal.hidden) closeModal(); });

function segmented(container, options, current, onPick) {
  container.innerHTML = options.map(o =>
    `<button type="button" data-v="${esc(o.value)}" class="${String(o.value) === String(current) ? "active" : ""}">${o.icon || ""}${esc(o.label)}</button>`
  ).join("");
  container.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    container.querySelectorAll("button").forEach(x => x.classList.toggle("active", x === b));
    onPick(b.dataset.v);
  });
}

function openAdd() {
  showModal("#tpl-add");
  let platform = "steam";
  const input = $("#add-query"), hint = $("#add-hint"), error = $("#add-error"), submit = $("#add-submit");
  const setPlatform = v => { platform = v; hint.textContent = HINTS[v] || ""; error.textContent = ""; input.focus(); };
  segmented($("#add-platforms"), S.platforms.map(p => ({ value: p.id, label: p.label, icon: platIcon(p.id) })), platform, setPlatform);
  setPlatform(platform);
  $("#add-form").addEventListener("submit", async e => {
    e.preventDefault();
    if (!input.value.trim() || submit.disabled) return;
    submit.disabled = true;
    submit.textContent = "Buscando…";
    error.textContent = "";
    const res = await api().add_player(platform, input.value);
    submit.disabled = false;
    submit.textContent = "Añadir";
    if (!res.ok) { error.textContent = res.error; input.select(); return; }
    S.players.push(res.player);
    closeModal();
    render();
  });
}

function openSettings() {
  showModal("#tpl-settings");
  segmented($("#set-refresh"), [2, 5, 10].map(m => ({ value: m, label: `${m} min` })), S.config.refresh_minutes,
    v => setOption("refresh_minutes", Number(v)));
  segmented($("#set-results"), [["day", "Hoy"], ["session", "Sesión"], ["both", "Ambos"]].map(([value, label]) => ({ value, label })),
    S.config.result_mode || "both", v => setOption("result_mode", v));
  const compact = $("#set-compact"), ontop = $("#set-ontop");
  compact.checked = !!S.config.compact;
  ontop.checked = !!S.config.on_top;
  compact.addEventListener("change", () => setOption("compact", compact.checked));
  ontop.addEventListener("change", () => setOption("on_top", ontop.checked));

  segmented($("#set-match-rank"), [["tab", "Pestaña elegida"], ["match", "Lista de la partida"]].map(([value, label]) => ({ value, label })),
    S.config.match_rank || "tab", v => setOption("match_rank", v));
  setupVersion();
  const live = $("#set-live");
  segmented(live, [["top", "Arriba"], ["bottom", "Abajo"], ["off", "No"]].map(([value, label]) => ({ value, label })),
    S.config.match_pos || "off", v => setOption("match_pos", v));
  $("#live-setup").addEventListener("click", async e => {
    const b = e.target.closest("[data-setup]");
    if (!b || b.disabled) return;
    const a = b.dataset.setup;
    if (a === "open") return api().open_game_config();
    b.disabled = true;
    const st = await api()[{ pick: "pick_game_dir", enable: "enable_stats_api", disable: "disable_stats_api" }[a]]();
    renderSetup(st, a);
  });
  api().get_live_setup().then(st => renderSetup(st));
}

// Estado de la Stats API en Ajustes (carpeta del juego, .ini, conexión).
let setupState = null;

function renderSetup(st, action) {
  const box = $("#live-setup");
  if (!box || !st) return;
  setupState = { ...st, done: false, error: null };
  const ini = st.ini || {};
  const [cls, text] = st.status === "connected" ? ["ok", "Conectado con Rocket League"]
    : ["", "Esperando al juego (cerrado o con la Stats API apagada)"];
  let h = `<p class="status ${cls}"><i></i>${text}</p>`;
  const btns = [];
  if (!st.dir) {
    h += `<p class="hint">No encontré Rocket League. Elige la carpeta del juego (la que tiene TAGame y Binaries).</p>`;
    btns.push(`<button type="button" class="link" data-setup="pick">Elegir carpeta…</button>`);
  } else {
    h += `<p class="path" title="${esc(st.dir)}">${esc(st.dir)}</p>`;
    if (!ini.file) {
      h += `<p class="hint">Esta versión del juego no trae DefaultStatsAPI.ini. Actualiza Rocket League.</p>`;
    } else if (ini.enabled) {
      h += `<p class="hint">Stats API activada en ${esc(ini.name)} (${ini.rate} por segundo, puerto ${ini.port}).</p>`;
      btns.push(`<button type="button" class="link" data-setup="disable">Desactivar</button>`);
    } else {
      h += `<p class="hint">La Stats API del juego viene apagada. «Activar» pone <b>PacketSendRate=${st.rate}</b> en TAGame\\Config\\${esc(ini.name)} y guarda una copia .bak. Es una función oficial del juego: no se toca su proceso. Después hay que reiniciar el juego.</p>`;
      btns.unshift(`<button type="button" class="primary" data-setup="enable">Activar Stats API</button>`);
    }
    btns.push(`<button type="button" class="link" data-setup="open">Abrir carpeta</button>`);
    btns.push(`<button type="button" class="link" data-setup="pick">Cambiar…</button>`);
  }
  h += `<div class="row-btns">${btns.join("")}</div>`;
  if (st.done) h += `<p class="ok-line">Hecho. ${action === "disable" ? "Se apagará" : "Funcionará"} al reiniciar Rocket League.</p>`;
  if (st.error) h += `<p class="error">${esc(st.error)}</p>`;
  box.innerHTML = h;
}

// ---------- actualizaciones (GitHub) ----------

const updateEl = $("#update");

/** Aviso fijo abajo: hay versión nueva. No mueve las tarjetas. */
function showUpdate(info) {
  S.update = info;
  updateEl.innerHTML = `<span>Nueva versión <b>${esc(info.latest)}</b> disponible</span>
    <button class="primary" data-up="install">Actualizar</button>
    <button class="link" data-up="close" title="Ahora no">✕</button>`;
  updateEl.title = info.notes || "";
  updateEl.hidden = false;
}

async function installUpdate() {
  updateEl.innerHTML = `<span>Actualizando a ${esc(S.update.latest)}… se volverá a abrir sola</span>`;
  updateEl.hidden = false;
  const res = await api().install_update();
  if (!res.ok) updateEl.innerHTML = `<span class="neg">${esc(res.error)}</span><button class="link" data-up="close">✕</button>`;
}

updateEl.addEventListener("click", e => {
  const b = e.target.closest("[data-up]");
  if (!b) return;
  if (b.dataset.up === "close") updateEl.hidden = true;
  if (b.dataset.up === "install") installUpdate();
});

function setupVersion() {
  $("#set-version").textContent = S.version || "";
  $("#set-github").addEventListener("click", () => api().open_repo());
  $("#set-check").addEventListener("click", async e => {
    const btn = e.currentTarget, out = $("#set-update");
    btn.disabled = true;
    out.textContent = "Buscando…";
    const r = await api().check_update();
    btn.disabled = false;
    if (!out.isConnected) return;
    if (r.error) { out.textContent = r.error; return; }
    if (!r.available) { out.textContent = `Tienes la última versión (${r.current}).`; return; }
    out.innerHTML = `Hay una versión nueva: <b>${esc(r.latest)}</b> <button type="button" class="link" id="set-install">Actualizar</button>`;
    $("#set-install").addEventListener("click", () => { closeModal(); showUpdate(r); installUpdate(); });
  });
}

// ---------- arranque y eventos de Python ----------

window.RLT = {
  onEvent(ev) {
    if (ev.type === "update") return showUpdate(ev.update);
    if (ev.type === "live") {
      S.live = ev.live || {};
      if (S.live.match && !S.live.match.ended) S.liveOpen = false;  // la próxima vez que acabe, plegada
      renderLive();
      updateRefreshIcon();
      if (S.live.match) ensureThresholds(S.live.match.playlist);
      if (setupState) renderSetup({ ...setupState, status: S.live.status });
      return;
    }
    if (ev.type !== "player") return;
    const i = S.players.findIndex(x => x.key === ev.player.key);
    if (i < 0) return;
    S.players[i] = ev.player;
    updateCard(ev.player.key);
  },
};

async function start() {
  try {
    const st = await api().get_state();
    Object.assign(S, { config: st.config, players: st.players, playlists: st.playlists, platforms: st.platforms, live: st.live || {}, version: st.version });
    for (const [k, rows] of Object.entries(st.thresholds || {})) S.thresholds[Number(k)] = rows;
    render();
    api().ready();
  } catch (e) {
    // Sin esto la ventana se queda en blanco y no se sabe por qué.
    list.innerHTML = `<div class="empty"><b>No se pudo cargar</b>${esc((e && e.message) || e)}<br>Cierra y vuelve a abrir la app.</div>`;
    return;
  }
  ensureThresholds(S.config.playlist);
  // Repinta de vez en cuando para que "hace X min" y "Hoy" no se queden viejos.
  setInterval(() => { if (modal.hidden && !drag) render(); }, 60000);
}

if (window.pywebview && window.pywebview.api) start();
else window.addEventListener("pywebviewready", start);
