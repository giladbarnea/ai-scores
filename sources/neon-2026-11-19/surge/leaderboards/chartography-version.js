
(function () {
  function el(h) { var t = document.createElement("template"); t.innerHTML = h.trim(); return t.content.firstElementChild; }
  function run() {
    var h1 = document.querySelector(".lead-hero-title h1");
    if (h1 && !h1.querySelector(".v2-chip")) h1.appendChild(el('<span class="v2-chip">v1.1</span>'));
    var btns = document.querySelector(".lead-hero-left .lead-hero-btns") || document.querySelector(".lead-hero-btns");
    if (btns && !document.querySelector(".hero-changelog")) btns.parentElement.insertBefore(el('<div class="hero-changelog"><div class="hero-changelog__head">Changelog</div><ol><li><span class="ver">v1.1</span> <span>Updated to use agentic harness.</span></li></ol></div>'), btns.nextSibling);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
