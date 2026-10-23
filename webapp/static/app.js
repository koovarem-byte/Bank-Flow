"use strict";

const tg = window.Telegram && window.Telegram.WebApp;
const view = document.getElementById("view");
const tabbar = document.getElementById("tabbar");

const state = { me: null, catalog: null, category: "all", sort: "reward" };

// ---------- helpers ----------

function esc(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function rub(value) {
  return Number(value || 0).toLocaleString("ru-RU") + " ₽";
}

function date(value) {
  if (!value) return "";
  const d = new Date(value);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

// Неразрывный пробел в суммах: «1 000 ₽» не разрывается переносом
function money(text) {
  return esc(text).replace(/(\d) (\d{3})/g, "$1\u00a0$2").replace(/ ₽/g, "\u00a0₽");
}

// Предупреждение о кредите без заголовка с эмодзи (заголовок рисуем сами)
function creditBody(text) {
  return tgHtml(String(text).split("\n\n").slice(1).join("\n\n"));
}

// Telegram-HTML (наши тексты из privacy.py / offers.py) -> HTML страницы
function tgHtml(text) {
  return String(text).replace(/\n/g, "<br>");
}

function haptic(type) {
  try { tg && tg.HapticFeedback && tg.HapticFeedback.notificationOccurred(type); } catch (e) { /* нет в браузере */ }
}

function toast(text) {
  const el = document.getElementById("toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, 3200);
}

const ICON = {
  shield: '<svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
  warn: '<svg viewBox="0 0 24 24"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17h.01"/></svg>',
  chevron: '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>',
  cards: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 10h18"/></svg>',
  out: '<svg viewBox="0 0 24 24"><path d="M12 19V5M6 11l6-6 6 6"/></svg>',
  list: '<svg viewBox="0 0 24 24"><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/></svg>',
  users: '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 19c1-3 3.5-4.5 6.5-4.5s5.5 1.5 6.5 4.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5c1.8.6 3 2 3.5 4.5"/></svg>',
  star: '<svg viewBox="0 0 24 24"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
  doc: '<svg viewBox="0 0 24 24"><path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5"/></svg>',
};

const APP_STATUS = {
  pending: ["На проверке", "wait"],
  approved: ["Подтверждена", "ok"],
  rejected: ["Отклонена", "bad"],
};

const WD_STATUS = {
  pending: ["Ожидает выплаты", "wait"],
  paid: ["Выплачено", "ok"],
  rejected: ["Отклонена", "bad"],
};

const LINK_STATUS = {
  pending: ["Ссылка готовится", "wait"],
  ready: ["Ссылка готова", "ok"],
};

function pill(map, status) {
  const [text, cls] = map[status] || [status, ""];
  return `<span class="pill ${cls}">${esc(text)}</span>`;
}

// ---------- API ----------

class ApiError extends Error {
  constructor(status, body) {
    super((body && body.message) || "Ошибка сети");
    this.status = status;
    this.code = body && body.error;
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: {
      "Authorization": "tma " + (tg ? tg.initData : ""),
      "Content-Type": "application/json",
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  let body = null;
  try { body = await response.json(); } catch (e) { /* пустой ответ */ }

  if (!response.ok) {
    if (response.status === 403 && body && body.error === "onboarding_required") {
      location.hash = "#/welcome";
    }
    throw new ApiError(response.status, body);
  }
  return body;
}

// ---------- sheet ----------

function openSheet(html) {
  const sheet = document.getElementById("sheet");
  sheet.innerHTML = html;
  sheet.hidden = false;
  document.getElementById("sheet-backdrop").hidden = false;
  return sheet;
}

function closeSheet() {
  document.getElementById("sheet").hidden = true;
  document.getElementById("sheet-backdrop").hidden = true;
}

document.getElementById("sheet-backdrop").addEventListener("click", closeSheet);

// ---------- screens ----------

// Вложенные экраны подсвечивают свой раздел в нижнем меню
const TAB_PARENT = { offer: "offers", withdraw: "cabinet", referrals: "cabinet", achievements: "cabinet", privacy: "cabinet" };

function setChrome(tab) {
  tabbar.hidden = !tab;
  view.classList.toggle("no-tabbar", !tab);
  const parent = TAB_PARENT[tab] || tab;
  tabbar.querySelectorAll("a").forEach((a) => a.classList.toggle("active", a.dataset.tab === parent));
  document.getElementById("topbar-note").textContent = "";

  if (tg && tg.BackButton) {
    const root = ["home", "offers", "applications", "cabinet"].includes(tab);
    if (root || !tab) tg.BackButton.hide(); else tg.BackButton.show();
  }
}

async function loadMe() {
  state.me = await api("/api/me");
  return state.me;
}

async function loadCatalog(force) {
  if (!state.catalog || force) state.catalog = await api("/api/offers");
  return state.catalog;
}

async function screenWelcome() {
  setChrome(null);
  const me = state.me || await loadMe();

  if (!me.onboarding.age_confirmed) {
    view.innerHTML = `
      <div class="hero">
        <div class="hero-badge">18+</div>
        <h1>BankFlow — только для 18+</h1>
        <p class="muted">Здесь собраны банковские и кредитные продукты. Оформлять их можно только совершеннолетним.</p>
      </div>
      <div class="notice">${ICON.shield}<div>${esc(SAFETY_FALLBACK)}</div></div>
      <div style="height:16px"></div>
      <button class="btn btn-primary" id="age-yes">Мне есть 18 лет</button>
      <button class="btn btn-ghost" id="age-no">Мне нет 18</button>`;

    document.getElementById("age-yes").onclick = async () => {
      await api("/api/onboarding/age", { method: "POST" });
      state.me.onboarding.age_confirmed = true;
      haptic("success");
      screenWelcome();
    };
    document.getElementById("age-no").onclick = () => {
      view.innerHTML = `
        <div class="hero">
          <div class="hero-badge">18+</div>
          <h1>BankFlow доступен только с 18 лет</h1>
          <p class="muted">Никому не передавайте свои карты, данные и коды из СМС — даже за вознаграждение.</p>
        </div>`;
    };
    return;
  }

  const privacy = await api("/api/privacy");

  view.innerHTML = `
    <div class="card legal">${tgHtml(privacy.consent)}</div>
    <div style="height:12px"></div>
    <button class="btn btn-ghost" id="read-policy">${ICON.doc} Политика конфиденциальности</button>
    <button class="btn btn-primary" id="consent">Даю согласие</button>
    <p class="muted small" style="text-align:center">Без согласия мы не сможем вести кабинет и делать выплаты.</p>`;

  document.getElementById("read-policy").onclick = () => showPolicy(privacy);
  document.getElementById("consent").onclick = async () => {
    await api("/api/onboarding/consent", { method: "POST" });
    state.me.onboarding.consent = true;
    haptic("success");
    location.hash = "#/home";
  };
}

const SAFETY_FALLBACK = "Оформляйте продукт только на себя. Никому не передавайте карту, данные и коды из СМС. BankFlow никогда не спрашивает пароли, коды и данные карт.";

function showPolicy(privacy) {
  openSheet(`
    <div class="legal">${privacy.parts.map(tgHtml).join("<br><br>")}</div>
    <div style="height:16px"></div>
    <button class="btn" id="sheet-close">Закрыть</button>`);
  document.getElementById("sheet-close").onclick = closeSheet;
}

async function screenHome() {
  setChrome("home");
  const me = await loadMe();
  const p = me.progress;

  view.innerHTML = `
    <h1>Привет, ${esc(me.first_name || "друг")}</h1>
    <section class="card balance-card">
      <div class="balance-label">Баланс</div>
      <div class="balance-value num">${rub(me.balance)}</div>
      <div class="stats">
        <div class="stat"><span class="muted small">Доступно к выводу</span><b class="num">${rub(me.available)}</b></div>
        <div class="stat"><span class="muted small">Заработано всего</span><b class="num">${rub(me.total_earned)}</b></div>
      </div>
    </section>

    <div class="actions">
      <a class="action" href="#/offers">${ICON.cards}Предложения</a>
      <a class="action" href="#/withdraw">${ICON.out}Вывести</a>
      <a class="action" href="#/applications">${ICON.list}Заявки</a>
    </div>

    <h2>Уровень</h2>
    <section class="card">
      <div class="row"><b>${esc(p.level)}</b><span class="muted small num">${me.points.toLocaleString("ru-RU")} ⭐</span></div>
      <div class="progress"><span style="width:${p.percent}%"></span></div>
      <div class="muted small">${p.next_level
        ? `До ${esc(p.next_level)}: <span class="num">${p.remaining.toLocaleString("ru-RU")}</span> ⭐`
        : "Максимальный уровень"}</div>
    </section>

    <h2>Безопасность</h2>
    <div class="notice">${ICON.shield}<div>${esc(SAFETY_FALLBACK)}</div></div>`;
}

function offerCard(offer) {
  const badges = [];
  if (offer.is_credit) badges.push('<span class="pill plain">Кредитный продукт</span>');
  if (offer.link_status) badges.push(pill(LINK_STATUS, offer.link_status));

  return `
    <a class="card offer" href="#/offer/${encodeURIComponent(offer.id)}">
      <div class="offer-top">
        <div>
          <div class="offer-name">${esc(offer.name)}</div>
          <div class="offer-type">${esc(offer.type)}</div>
        </div>
        <div class="offer-reward num">${rub(offer.reward)}</div>
      </div>
      ${badges.length ? `<div class="offer-meta">${badges.join("")}</div>` : ""}
    </a>`;
}

async function screenOffers() {
  setChrome("offers");
  const catalog = await loadCatalog(true);

  const render = () => {
    let list = catalog.offers.filter((o) => state.category === "all" || o.category === state.category);
    list = list.slice().sort((a, b) => state.sort === "reward" ? b.reward - a.reward : a.name.localeCompare(b.name, "ru"));

    const chips = [{ id: "all", name: "Все" }].concat(catalog.categories)
      .map((c) => `<button class="chip ${state.category === c.id ? "active" : ""}" data-cat="${esc(c.id)}">${esc(c.name)}</button>`)
      .join("");

    view.innerHTML = `
      <h1>Предложения</h1>
      <div class="chips">${chips}</div>
      <div class="toolbar">
        <span class="muted small">${list.length} ${plural(list.length, "предложение", "предложения", "предложений")}</span>
        <select class="select" id="sort" aria-label="Сортировка">
          <option value="reward" ${state.sort === "reward" ? "selected" : ""}>Сначала дороже</option>
          <option value="name" ${state.sort === "name" ? "selected" : ""}>По названию</option>
        </select>
      </div>
      ${list.length ? list.map(offerCard).join("") : `<div class="empty"><b>Пока пусто</b>В этом разделе скоро появятся предложения.</div>`}`;

    view.querySelectorAll(".chip").forEach((el) => {
      el.onclick = () => { state.category = el.dataset.cat; render(); };
    });
    document.getElementById("sort").onchange = (e) => { state.sort = e.target.value; render(); };
  };

  render();
}

function plural(n, one, few, many) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

function adBlock(offer) {
  const parts = [`Реклама. Рекламодатель: <b>${esc(offer.ad.advertiser)}</b>`];
  if (offer.ad.erid) parts.push(`erid: ${esc(offer.ad.erid)}`);
  let html = parts.join(" · ");
  if (offer.ad.terms_url) {
    html += `<br><a href="${esc(offer.ad.terms_url)}" data-external>Полные условия банка</a>`;
  }
  return `<div class="ad">${html}</div>`;
}

async function screenOffer(id) {
  setChrome("offer");
  const catalog = await loadCatalog(true);
  const offer = catalog.offers.find((o) => o.id === id);

  if (!offer) {
    view.innerHTML = `<div class="empty"><b>Предложение не найдено</b><a href="#/offers">К предложениям</a></div>`;
    return;
  }

  const reqs = offer.requirements.length
    ? `<h2>Для оформления понадобятся</h2><div class="card"><ul class="clean">${offer.requirements.map((r) => `<li>${esc(r)}</li>`).join("")}</ul></div>`
    : "";

  let actions;
  if (offer.link_status === "ready" && offer.link) {
    actions = `
      <button class="btn btn-primary" id="go">Перейти к оформлению ↗</button>
      <button class="btn" id="done">Я выполнил условия</button>`;
  } else if (offer.link_status === "pending") {
    actions = `<div class="notice">${ICON.doc}<div>Ссылка готовится. Когда она будет готова, бот пришлёт сообщение, а здесь появится кнопка оформления.</div></div>`;
  } else if (offer.flow === "bot") {
    actions = `<button class="btn btn-primary" id="via-bot">Оформить через бот</button>
      <p class="muted small">Для этого предложения нужно подтвердить статус ИП — это делается в разделе «Для бизнеса» в боте.</p>`;
  } else {
    actions = `<button class="btn btn-primary" id="get-link">Получить ссылку</button>`;
  }

  view.innerHTML = `
    <div class="offer-type">${esc(offer.type)}</div>
    <h1 style="margin-top:2px">${esc(offer.name)}</h1>
    <section class="card">
      <div class="muted small">Вознаграждение</div>
      <div class="detail-reward num">${rub(offer.reward)}</div>
      <div class="muted small">Начисляется после проверки выполнения условий</div>
    </section>

    <h2>Условие</h2>
    <div class="card">${money(offer.condition)}</div>
    ${offer.link_comment ? `<h2>Комментарий администратора</h2><div class="card">${esc(offer.link_comment)}</div>` : ""}
    ${reqs}

    <div style="height:16px"></div>
    ${offer.is_credit ? `<div class="notice warn">${ICON.warn}<div><b>Это кредитный продукт</b><br>${creditBody(catalog.credit_warning)}</div></div><div style="height:12px"></div>` : ""}
    ${actions}

    <div style="height:16px"></div>
    <div class="notice">${ICON.shield}<div>${esc(catalog.safety_rule)}</div></div>
    ${adBlock(offer)}`;

  const getLink = document.getElementById("get-link");
  if (getLink) getLink.onclick = () => startLinkFlow(offer, catalog);

  const go = document.getElementById("go");
  if (go) go.onclick = () => openExternal(offer.link);

  const done = document.getElementById("done");
  if (done) done.onclick = () => confirmDone(offer);

  const viaBot = document.getElementById("via-bot");
  if (viaBot) viaBot.onclick = () => (tg ? tg.close() : null);

  view.querySelectorAll("[data-external]").forEach((a) => {
    a.onclick = (e) => { e.preventDefault(); openExternal(a.getAttribute("href")); };
  });
}

function openExternal(url) {
  if (tg && tg.openLink) tg.openLink(url); else window.open(url, "_blank", "noopener");
}

function startLinkFlow(offer, catalog) {
  if (offer.is_credit) {
    openSheet(`
      <h1>Это кредитный продукт</h1>
      <div class="notice warn">${ICON.warn}<div>${creditBody(catalog.credit_warning)}</div></div>
      <div style="height:16px"></div>
      <button class="btn btn-primary" id="continue">Понятно, продолжить</button>
      <button class="btn btn-ghost" id="cancel">Отмена</button>`);
    document.getElementById("cancel").onclick = closeSheet;
    document.getElementById("continue").onclick = () => {
      closeSheet();
      offer.flow === "personal" ? personalForm(offer) : requestLink(offer, {});
    };
    return;
  }
  offer.flow === "personal" ? personalForm(offer) : requestLink(offer, {});
}

function personalForm(offer) {
  const sheet = openSheet(`
    <h1>Персональная ссылка</h1>
    <p class="muted small">Данные нужны, чтобы подготовить ссылку на ${esc(offer.name)}. Используются по политике конфиденциальности.</p>
    <form id="pform" novalidate>
      <label class="field"><span>ФИО полностью</span><input class="input" name="fio" autocomplete="name" required></label>
      <label class="field"><span>Email</span><input class="input" name="email" type="email" inputmode="email" autocomplete="email" required></label>
      <label class="field"><span>Телефон</span><input class="input" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 999 123-45-67" required></label>
      <div class="form-error" id="perr"></div>
      <button class="btn btn-primary" type="submit">Отправить</button>
      <button class="btn btn-ghost" type="button" id="pcancel">Отмена</button>
    </form>`);

  document.getElementById("pcancel").onclick = closeSheet;
  sheet.querySelector("#pform").onsubmit = async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const body = { fio: form.get("fio"), email: form.get("email"), phone: form.get("phone") };
    try {
      await requestLink(offer, body, true);
    } catch (err) {
      document.getElementById("perr").textContent = err.message;
    }
  };
}

async function requestLink(offer, body, rethrow) {
  try {
    await api(`/api/offers/${encodeURIComponent(offer.id)}/link`, { method: "POST", body });
    closeSheet();
    haptic("success");
    toast("Запрос отправлен. Бот пришлёт ссылку, когда она будет готова.");
    screenOffer(offer.id);
  } catch (err) {
    if (rethrow) throw err;
    toast(err.message);
  }
}

function confirmDone(offer) {
  openSheet(`
    <h1>Условия выполнены?</h1>
    <p class="muted">${money(offer.condition)}</p>
    <p class="muted small">Заявка уйдёт на проверку. Вознаграждение начислим после подтверждения.</p>
    <button class="btn btn-primary" id="yes">Да, отправить на проверку</button>
    <button class="btn btn-ghost" id="no">Ещё нет</button>`);
  document.getElementById("no").onclick = closeSheet;
  document.getElementById("yes").onclick = async () => {
    try {
      await api(`/api/offers/${encodeURIComponent(offer.id)}/done`, { method: "POST" });
      closeSheet();
      haptic("success");
      location.hash = "#/applications";
    } catch (err) {
      closeSheet();
      toast(err.message);
    }
  };
}

async function screenApplications() {
  setChrome("applications");
  const { applications } = await api("/api/applications");

  if (!applications.length) {
    view.innerHTML = `<h1>Заявки</h1>
      <div class="empty"><b>Заявок пока нет</b>Выберите предложение, оформите продукт и нажмите «Я выполнил условия».</div>
      <a class="btn btn-primary" href="#/offers">К предложениям</a>`;
    return;
  }

  view.innerHTML = `<h1>Заявки</h1>` + applications.map((a) => `
    <section class="card">
      <div class="row">
        <div><div class="offer-name">${esc(a.offer_name)}</div>
        <div class="muted small">№${a.id}${a.created_at ? " · " + date(a.created_at) : ""}</div></div>
        <div class="offer-reward num" style="font-size:18px">${rub(a.reward)}</div>
      </div>
      <div class="offer-meta">${pill(APP_STATUS, a.status)}</div>
      ${a.comment ? `<div class="notice" style="margin-top:12px">${ICON.doc}<div>${esc(a.comment)}</div></div>` : ""}
    </section>`).join("");
}

async function screenWithdraw() {
  setChrome("withdraw");
  const [me, history] = await Promise.all([loadMe(), api("/api/withdrawals")]);

  view.innerHTML = `
    <h1>Вывод средств</h1>
    <section class="card balance-card">
      <div class="balance-label">Доступно к выводу</div>
      <div class="balance-value num" style="margin-bottom:0">${rub(me.available)}</div>
    </section>

    <h2>Новая выплата по СБП</h2>
    <form class="card" id="wform" novalidate>
      <label class="field"><span>Сумма, ₽</span><input class="input num" name="amount" inputmode="numeric" placeholder="1000"></label>
      <label class="field"><span>Телефон, привязанный к СБП</span><input class="input" name="phone" type="tel" inputmode="tel" placeholder="+7 999 123-45-67"></label>
      <label class="field"><span>Банк</span><input class="input" name="bank" placeholder="Например, Сбербанк"></label>
      <div class="form-error" id="werr"></div>
      <button class="btn btn-primary" type="submit" ${me.available > 0 ? "" : "disabled"}>Создать заявку</button>
    </form>

    <h2>История</h2>
    ${history.withdrawals.length ? `<div class="card list-card">${history.withdrawals.map((w) => `
      <div class="list-item">
        <div class="grow"><b class="num">${rub(w.amount)}</b><div class="muted small">№${w.id} · ${esc(w.bank || "")}</div></div>
        ${pill(WD_STATUS, w.status)}
      </div>`).join("")}</div>` : `<div class="empty">Выплат ещё не было</div>`}`;

  document.getElementById("wform").onsubmit = async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      await api("/api/withdrawals", {
        method: "POST",
        body: { amount: form.get("amount"), phone: form.get("phone"), bank: form.get("bank") },
      });
      haptic("success");
      toast("Заявка на выплату создана");
      screenWithdraw();
    } catch (err) {
      document.getElementById("werr").textContent = err.message;
      haptic("error");
    }
  };
}

async function screenCabinet() {
  setChrome("cabinet");
  const me = await loadMe();

  view.innerHTML = `
    <h1>Кабинет</h1>
    <section class="card">
      <div class="row"><span class="muted">Telegram ID</span><span class="num">${me.id}</span></div>
    </section>
    <div style="height:10px"></div>
    <section class="card list-card">
      <a class="list-item" href="#/withdraw">${ICON.out}<div class="grow">Вывод средств<div class="muted small">Доступно ${rub(me.available)}</div></div>${ICON.chevron}</a>
      <a class="list-item" href="#/referrals">${ICON.users}<div class="grow">Партнёрская программа<div class="muted small">25% от подтверждённых заявок друзей</div></div>${ICON.chevron}</a>
      <a class="list-item" href="#/achievements">${ICON.star}<div class="grow">Достижения</div>${ICON.chevron}</a>
      <a class="list-item" href="#/privacy">${ICON.doc}<div class="grow">Политика конфиденциальности</div>${ICON.chevron}</a>
    </section>`;
}

async function screenReferrals() {
  setChrome("referrals");
  const r = await api("/api/referrals");

  view.innerHTML = `
    <h1>Партнёрская программа</h1>
    <p class="muted">Приглашайте друзей и получайте ${r.percent}% от их подтверждённых заявок.</p>
    <div class="stats">
      <div class="stat"><span class="muted small">Приглашено</span><b class="num">${r.invited}</b></div>
      <div class="stat"><span class="muted small">Выполнили условия</span><b class="num">${r.active}</b></div>
    </div>
    <h2>Ваша ссылка</h2>
    <div class="card small" style="word-break:break-all">${esc(r.link)}</div>
    <div style="height:12px"></div>
    <button class="btn btn-primary" id="share">Пригласить друга</button>
    <button class="btn btn-ghost" id="copy">Скопировать ссылку</button>`;

  document.getElementById("share").onclick = () => {
    const url = "https://t.me/share/url?url=" + encodeURIComponent(r.link);
    if (tg && tg.openTelegramLink) tg.openTelegramLink(url); else window.open(url, "_blank", "noopener");
  };
  document.getElementById("copy").onclick = async () => {
    try { await navigator.clipboard.writeText(r.link); toast("Ссылка скопирована"); }
    catch (e) { toast("Не удалось скопировать — выделите ссылку вручную"); }
  };
}

async function screenAchievements() {
  setChrome("achievements");
  const { achievements } = await api("/api/achievements");

  view.innerHTML = `<h1>Достижения</h1><div class="ach">` + achievements.map((a) => `
    <div class="card ${a.earned_at ? "" : "locked"}">
      ${a.earned_at ? '<span class="pill ok">Получено</span>' : '<span class="pill plain">Закрыто</span>'}
      <div class="ach-title">${esc(a.title)}</div>
      <div class="muted small">${esc(a.description)}</div>
      <div class="small" style="margin-top:6px">+${a.reward} ⭐</div>
    </div>`).join("") + `</div>`;
}

async function screenPrivacy() {
  setChrome("privacy");
  const privacy = await api("/api/privacy");
  view.innerHTML = `<div class="card legal">${privacy.parts.map(tgHtml).join("<br><br>")}</div>`;
}

// ---------- router ----------

const routes = [
  [/^#\/welcome$/, screenWelcome],
  [/^#\/home$/, screenHome],
  [/^#\/offers$/, screenOffers],
  [/^#\/offer\/(.+)$/, (m) => screenOffer(decodeURIComponent(m[1]))],
  [/^#\/applications$/, screenApplications],
  [/^#\/withdraw$/, screenWithdraw],
  [/^#\/cabinet$/, screenCabinet],
  [/^#\/referrals$/, screenReferrals],
  [/^#\/achievements$/, screenAchievements],
  [/^#\/privacy$/, screenPrivacy],
];

async function route() {
  closeSheet();
  const hash = location.hash || "#/home";

  if (state.me && !(state.me.onboarding.age_confirmed && state.me.onboarding.consent) && hash !== "#/welcome") {
    location.hash = "#/welcome";
    return;
  }

  if (state.me && state.me.onboarding.age_confirmed && state.me.onboarding.consent && hash === "#/welcome") {
    location.hash = "#/home";
    return;
  }

  const found = routes.find(([re]) => re.test(hash));
  if (!found) { location.hash = "#/home"; return; }

  view.innerHTML = '<div class="loader"><span></span></div>';
  window.scrollTo(0, 0);

  try {
    await found[1](hash.match(found[0]));
  } catch (err) {
    if (err.code === "onboarding_required") return;
    view.innerHTML = `<div class="empty"><b>Не получилось загрузить</b>${esc(err.message)}</div>
      <button class="btn" onclick="location.reload()">Обновить</button>`;
  }
}

async function start() {
  if (!tg || !tg.initData) {
    tabbar.hidden = true;
    view.innerHTML = `<div class="hero"><div class="hero-badge">BF</div>
      <h1>Откройте BankFlow в Telegram</h1>
      <p class="muted">Приложение работает внутри Telegram — откройте его из бота.</p></div>`;
    return;
  }

  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor("#0a0e13");
    tg.setBackgroundColor("#0a0e13");
  } catch (e) { /* старые клиенты */ }
  if (tg.BackButton) tg.BackButton.onClick(() => history.back());

  try {
    await loadMe();
  } catch (err) {
    view.innerHTML = `<div class="empty"><b>Не получилось войти</b>${esc(err.message)}</div>`;
    return;
  }

  const ok = state.me.onboarding.age_confirmed && state.me.onboarding.consent;
  if (!ok) location.hash = "#/welcome";

  window.addEventListener("hashchange", route);
  route();
}

start();
