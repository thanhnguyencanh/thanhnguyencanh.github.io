/* Progressive enhancement: all pages and publications remain readable without JS. */
(() => {
  "use strict";

  const normalize = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const tokens = (value) => normalize(value).trim().split(/\s+/).filter(Boolean);
  const matches = (value, query) => tokens(query).every((word) => normalize(value).includes(word));

  const navigation = document.getElementById("site-nav");
  const menu = document.querySelector(".nav-toggle");
  const closeMenu = () => {
    navigation.classList.remove("is-open");
    menu.setAttribute("aria-expanded", "false");
    menu.setAttribute("aria-label", "Open navigation");
  };
  menu.addEventListener("click", () => {
    const expanded = menu.getAttribute("aria-expanded") !== "true";
    menu.setAttribute("aria-expanded", String(expanded));
    menu.setAttribute("aria-label", expanded ? "Close navigation" : "Open navigation");
    navigation.classList.toggle("is-open", expanded);
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".site-header")) closeMenu();
  });
  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });

  const themeButton = document.getElementById("theme-toggle");
  const updateThemeLabel = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    themeButton.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} theme`);
    themeButton.setAttribute("aria-pressed", String(dark));
    themeButton.querySelector("svg").innerHTML = dark
      ? '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'
      : '<path d="M20.5 14A8.5 8.5 0 0 1 10 3.5 8.5 8.5 0 1 0 20.5 14Z"/>';
  };
  themeButton.hidden = false;
  updateThemeLabel();
  themeButton.addEventListener("click", () => {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch (_) { /* Storage may be unavailable. */ }
    updateThemeLabel();
  });

  const newsToggle = document.getElementById("toggle-news");
  if (newsToggle) {
    const items = [...document.querySelectorAll(".news-item")];
    const visibleCount = 5;
    let expanded = false;
    const updateNews = () => {
      const targetId = location.hash.slice(1);
      items.forEach((item, index) => { item.hidden = !expanded && index >= visibleCount && item.id !== targetId; });
      newsToggle.textContent = expanded ? "Show less news" : `Show all ${items.length} updates`;
      newsToggle.setAttribute("aria-expanded", String(expanded));
    };
    if (items.length > visibleCount) {
      newsToggle.hidden = false;
      updateNews();
      newsToggle.addEventListener("click", () => { expanded = !expanded; updateNews(); });
      window.addEventListener("hashchange", updateNews);
    }
  }

  const filters = document.getElementById("publication-filters");
  if (filters) {
    document.querySelector(".publication-toolbar").hidden = false;
    const query = document.getElementById("publication-query");
    const year = document.getElementById("publication-year");
    const type = document.getElementById("publication-type");
    const chips = [...document.querySelectorAll(".filter-chip")];
    const cards = [...document.querySelectorAll(".publication-card")];
    const count = document.getElementById("publication-count");
    const empty = document.getElementById("publication-empty");
    let topic = "all";
    const applyFilters = (updateUrl = true) => {
      let visible = 0;
      cards.forEach((card) => {
        const keep = matches(card.dataset.search, query.value)
          && (year.value === "all" || year.value === card.dataset.year)
          && (type.value === "all" || type.value === card.dataset.type)
          && (topic === "all" || card.dataset.topics.split("|").some((tag) => normalize(tag).includes(normalize(topic))));
        card.hidden = !keep;
        if (keep) visible++;
      });
      document.querySelectorAll(".year-group, .publication-group").forEach((group) => {
        group.hidden = ![...group.querySelectorAll(".publication-card")].some((card) => !card.hidden);
      });
      count.textContent = `${visible} of ${cards.length} publication${cards.length === 1 ? "" : "s"}`;
      empty.hidden = visible !== 0;
      chips.forEach((chip) => chip.setAttribute("aria-pressed", String(chip.dataset.topic === topic)));
      if (updateUrl) {
        const url = new URL(location.href);
        for (const [key, value] of [["q", query.value.trim()], ["year", year.value], ["type", type.value], ["topic", topic]]) {
          if (value && value !== "all") url.searchParams.set(key, value);
          else url.searchParams.delete(key);
        }
        try { history.replaceState(null, "", url); } catch (_) { /* Direct file previews may restrict history. */ }
      }
    };
    const loadFilters = () => {
      const params = new URLSearchParams(location.search);
      query.value = params.get("q") || "";
      year.value = [...year.options].some((option) => option.value === params.get("year")) ? params.get("year") : "all";
      type.value = [...type.options].some((option) => option.value === params.get("type")) ? params.get("type") : "all";
      topic = chips.some((chip) => chip.dataset.topic === params.get("topic")) ? params.get("topic") : "all";
      applyFilters(false);
    };
    filters.addEventListener("submit", (event) => event.preventDefault());
    query.addEventListener("input", () => applyFilters());
    year.addEventListener("change", () => applyFilters());
    type.addEventListener("change", () => applyFilters());
    chips.forEach((chip) => chip.addEventListener("click", () => { topic = chip.dataset.topic; applyFilters(); }));
    document.getElementById("reset-publications").addEventListener("click", () => {
      query.value = "";
      year.value = "all";
      type.value = "all";
      topic = "all";
      applyFilters();
      query.focus();
    });
    window.addEventListener("popstate", loadFilters);
    loadFilters();
  }

  document.querySelectorAll(".copy-citation").forEach((button) => {
    if (!navigator.clipboard) return;
    button.hidden = false;
    button.addEventListener("click", async () => {
      const code = button.parentElement.querySelector("code");
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = "Copied";
      } catch (_) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(code);
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = "Select and copy the citation";
      }
      setTimeout(() => { button.textContent = "Copy citation"; }, 2500);
    });
  });

  const dialog = document.getElementById("site-search");
  const searchButton = document.getElementById("open-search");
  const siteQuery = document.getElementById("site-query");
  const results = document.getElementById("site-search-results");
  const status = document.getElementById("site-search-count");
  const index = window.siteSearch || [];
  const makeText = (tag, className, value) => {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = value;
    return element;
  };
  const showResults = () => {
    results.replaceChildren();
    const words = tokens(siteQuery.value);
    if (!words.length) {
      status.textContent = "Type a title, author, topic or keyword.";
      return;
    }
    const found = index.filter((entry) => matches(`${entry.title} ${entry.category} ${entry.text}`, siteQuery.value));
    found.sort((a, b) => {
      const score = (entry) => words.reduce((sum, word) => sum + (normalize(entry.title).includes(word) ? 3 : 0), 0) + (entry.category === "Publication" ? 1 : 0);
      return score(b) - score(a);
    });
    status.textContent = found.length ? `${found.length} results${found.length > 20 ? " · showing the first 20" : ""}` : "No results. Try another keyword.";
    found.slice(0, 20).forEach((entry) => {
      const link = document.createElement("a");
      link.className = "search-result";
      link.href = dialog.dataset.root + entry.url;
      link.append(makeText("span", "search-result-type", entry.category), makeText("span", "search-result-title", entry.title), makeText("span", "search-result-excerpt", entry.text.slice(0, 170) + (entry.text.length > 170 ? "…" : "")));
      results.append(link);
    });
  };
  if (typeof dialog.showModal === "function") {
    searchButton.hidden = false;
    searchButton.addEventListener("click", () => {
      if (!dialog.open) dialog.showModal();
      closeMenu();
      siteQuery.focus();
    });
    document.getElementById("close-search").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      const box = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom)) dialog.close();
    });
    dialog.addEventListener("close", () => { searchButton.focus(); });
    siteQuery.addEventListener("input", showResults);
    dialog.querySelector("form").addEventListener("submit", (event) => {
      event.preventDefault();
      const first = results.querySelector("a");
      if (first) first.click();
    });
    document.addEventListener("keydown", (event) => {
      const editing = event.target.closest("input, textarea, select, [contenteditable]");
      if ((event.key.toLowerCase() === "k" && (event.ctrlKey || event.metaKey)) || (event.key === "/" && !editing && !event.ctrlKey && !event.metaKey && !event.altKey)) {
        event.preventDefault();
        searchButton.click();
      }
      if (event.key === "Escape") closeMenu();
    });
  }
})();
