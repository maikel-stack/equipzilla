// Widget de chat "Asesor de compra" de Equipzilla.
// Para incrustarlo en cualquier web (equipzilla.com incluida):
//   <script src="https://equipzilla-quiz.vercel.app/widget.js" defer></script>
// Habla con /api/chat en el mismo dominio del script.
(function () {
  if (window.__ezChatLoaded) return;
  window.__ezChatLoaded = true;

  var API = "/api/chat";
  try {
    var src = document.currentScript && document.currentScript.src;
    if (src) API = new URL(src).origin + "/api/chat";
  } catch (e) {}

  var BRAND = "#387E7F", DARK = "#17323A", ACCENT = "#8FD3C0";
  var GREETING =
    "👋 Hola, soy el **asesor de compra** de Equipzilla. Cuéntame qué necesitas " +
    "hacer — o qué máquina tienes en mente — y te digo qué te encaja de nuestro " +
    "stock de ocasión.";

  var history = [];
  try {
    var saved = sessionStorage.getItem("ezchat");
    if (saved) history = JSON.parse(saved) || [];
  } catch (e) {}

  var css = document.createElement("style");
  css.textContent =
    "#ez-chat-btn{position:fixed;bottom:22px;right:22px;z-index:99998;width:58px;height:58px;border-radius:50%;background:" + BRAND + ";border:none;cursor:pointer;box-shadow:0 6px 24px rgba(20,40,40,.35);display:flex;align-items:center;justify-content:center;transition:transform .15s}" +
    "#ez-chat-btn:hover{transform:scale(1.06)}" +
    "#ez-chat-panel{position:fixed;bottom:94px;right:22px;z-index:99999;width:370px;max-width:calc(100vw - 24px);height:560px;max-height:calc(100vh - 120px);background:#fff;border-radius:16px;box-shadow:0 12px 48px rgba(20,40,40,.35);display:none;flex-direction:column;overflow:hidden;font-family:system-ui,-apple-system,Segoe UI,sans-serif}" +
    "#ez-chat-panel.open{display:flex}" +
    "#ez-chat-head{background:" + DARK + ";color:#fff;padding:14px 18px}" +
    "#ez-chat-head b{font-size:15px;display:block}" +
    "#ez-chat-head span{font-size:12px;color:" + ACCENT + "}" +
    "#ez-chat-msgs{flex:1;overflow-y:auto;padding:14px;background:#F4F6F7;display:flex;flex-direction:column;gap:10px}" +
    ".ez-m{max-width:85%;padding:9px 13px;border-radius:14px;font-size:13.5px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word}" +
    ".ez-m.bot{background:#fff;color:#14181C;border:1px solid #E1E6E9;border-bottom-left-radius:4px;align-self:flex-start}" +
    ".ez-m.user{background:" + BRAND + ";color:#fff;border-bottom-right-radius:4px;align-self:flex-end}" +
    ".ez-m a{color:" + BRAND + ";font-weight:600}" +
    ".ez-typing{align-self:flex-start;background:#fff;border:1px solid #E1E6E9;border-radius:14px;padding:12px 16px;display:flex;gap:5px}" +
    ".ez-typing i{width:7px;height:7px;border-radius:50%;background:#9FB0B5;animation:ezb 1.2s infinite}" +
    ".ez-typing i:nth-child(2){animation-delay:.2s}.ez-typing i:nth-child(3){animation-delay:.4s}" +
    "@keyframes ezb{0%,60%,100%{opacity:.3;transform:translateY(0)}30%{opacity:1;transform:translateY(-4px)}}" +
    "#ez-chat-form{display:flex;gap:8px;padding:12px;background:#fff;border-top:1px solid #E1E6E9}" +
    "#ez-chat-in{flex:1;border:1px solid #CBD5D9;border-radius:22px;padding:10px 15px;font-size:13.5px;outline:none;font-family:inherit}" +
    "#ez-chat-in:focus{border-color:" + BRAND + "}" +
    "#ez-chat-send{background:" + BRAND + ";border:none;color:#fff;width:40px;height:40px;border-radius:50%;cursor:pointer;font-size:16px;flex:0 0 auto}" +
    "#ez-chat-send:disabled{opacity:.5;cursor:default}" +
    "@media(max-width:480px){#ez-chat-panel{right:12px;bottom:86px}}";
  document.head.appendChild(css);

  var btn = document.createElement("button");
  btn.id = "ez-chat-btn";
  btn.setAttribute("aria-label", "Abrir chat de asesoramiento");
  btn.innerHTML =
    '<svg width="27" height="27" viewBox="0 0 24 24" fill="none"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H9l-4.2 3.6c-.5.4-1.3.1-1.3-.6L3.5 16A2.5 2.5 0 0 1 4 13.5v-8Z" fill="#fff"/><circle cx="8.5" cy="9.5" r="1.2" fill="' + BRAND + '"/><circle cx="12" cy="9.5" r="1.2" fill="' + BRAND + '"/><circle cx="15.5" cy="9.5" r="1.2" fill="' + BRAND + '"/></svg>';

  var panel = document.createElement("div");
  panel.id = "ez-chat-panel";
  panel.innerHTML =
    '<div id="ez-chat-head"><b>Asesor de compra · Equipzilla</b><span>Te ayudamos a elegir la máquina adecuada</span></div>' +
    '<div id="ez-chat-msgs"></div>' +
    '<form id="ez-chat-form"><input id="ez-chat-in" type="text" autocomplete="off" placeholder="Cuéntanos qué necesitas hacer…" maxlength="1000"><button id="ez-chat-send" type="submit" aria-label="Enviar">➤</button></form>';

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var msgs = panel.querySelector("#ez-chat-msgs");
  var form = panel.querySelector("#ez-chat-form");
  var input = panel.querySelector("#ez-chat-in");
  var send = panel.querySelector("#ez-chat-send");

  function render(text) {
    var t = String(text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
      .replace(/\b(6\d{2}\s?\d{3}\s?\d{3}|9\d{2}\s?\d{3}\s?\d{3})\b/g,
        '<a href="tel:+34$1">$1</a>');
    return t;
  }

  function add(role, text) {
    var d = document.createElement("div");
    d.className = "ez-m " + (role === "user" ? "user" : "bot");
    d.innerHTML = render(text);
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function typing(on) {
    var t = msgs.querySelector(".ez-typing");
    if (on && !t) {
      t = document.createElement("div");
      t.className = "ez-typing";
      t.innerHTML = "<i></i><i></i><i></i>";
      msgs.appendChild(t);
      msgs.scrollTop = msgs.scrollHeight;
    } else if (!on && t) t.remove();
  }

  function save() {
    try { sessionStorage.setItem("ezchat", JSON.stringify(history.slice(-40))); } catch (e) {}
  }

  function paint() {
    msgs.innerHTML = "";
    add("bot", GREETING);
    history.forEach(function (m) { add(m.role, m.content); });
  }

  btn.addEventListener("click", function () {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) {
      if (!msgs.children.length) paint();
      input.focus();
    }
  });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var text = input.value.trim();
    if (!text || send.disabled) return;
    input.value = "";
    history.push({ role: "user", content: text });
    add("user", text);
    save();
    send.disabled = true;
    typing(true);
    fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        typing(false);
        var reply = (data && data.reply) ||
          "Se nos ha cruzado un cable 🙈 Escríbenos por WhatsApp al **606 836 581** y seguimos por ahí.";
        history.push({ role: "assistant", content: reply });
        add("bot", reply);
        save();
      })
      .catch(function () {
        typing(false);
        add("bot", "No consigo conectar ahora mismo. Escríbenos por WhatsApp al **606 836 581** o llama al **911 238 750** 📞");
      })
      .finally(function () {
        send.disabled = false;
        input.focus();
      });
  });
})();
