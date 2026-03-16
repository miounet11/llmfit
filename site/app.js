const yearNodes = document.querySelectorAll(".year");
yearNodes.forEach((node) => {
  node.textContent = new Date().getFullYear();
});

const normalizePath = (path) => {
  const cleaned = (path || "/").replace(/index\.html$/, "");
  return cleaned.endsWith("/") ? cleaned : `${cleaned}/`;
};

const getLanguagePaths = () => {
  const currentPath = normalizePath(window.location.pathname);
  const isChinesePath = currentPath === "/zh/" || currentPath.startsWith("/zh/");
  const englishPath = isChinesePath
    ? normalizePath(currentPath.replace(/^\/zh(?=\/)/, "") || "/")
    : currentPath;
  const chinesePath = isChinesePath
    ? currentPath
    : `/zh${currentPath === "/" ? "/" : currentPath}`;

  return {
    currentPath,
    englishPath,
    chinesePath,
    currentLanguage: isChinesePath ? "zh" : "en",
  };
};

const safeStorage = {
  get(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  },
  set(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      return null;
    }
    return value;
  },
};

const languagePreferenceKey = "llmfit_lang";
const languagePaths = getLanguagePaths();
const storedLanguage = safeStorage.get(languagePreferenceKey);
const browserLanguages = window.navigator.languages || [window.navigator.language || "en"];
const browserPrefersChinese = browserLanguages.some((language) => /^zh\b/i.test(language));

if (storedLanguage === "zh" && languagePaths.currentLanguage !== "zh") {
  window.location.replace(languagePaths.chinesePath);
} else if (storedLanguage === "en" && languagePaths.currentLanguage !== "en") {
  window.location.replace(languagePaths.englishPath);
} else if (!storedLanguage && browserPrefersChinese && languagePaths.currentLanguage !== "zh") {
  window.location.replace(languagePaths.chinesePath);
}

const page = document.body.dataset.page;
if (page) {
  const activeLink = document.querySelector(`[data-page-link="${page}"]`);
  if (activeLink) {
    activeLink.classList.add("is-active");
  }
}

document.querySelectorAll("[data-lang-link]").forEach((link) => {
  const targetLanguage = link.dataset.langLink;
  const href = targetLanguage === "zh"
    ? languagePaths.chinesePath
    : languagePaths.englishPath;

  link.href = href;
  link.classList.toggle("is-active", targetLanguage === languagePaths.currentLanguage);
  if (targetLanguage === languagePaths.currentLanguage) {
    link.setAttribute("aria-current", "page");
  }

  link.addEventListener("click", () => {
    safeStorage.set(languagePreferenceKey, targetLanguage);
  });
});

const navToggle = document.querySelector(".nav-toggle");
const topbarShell = document.querySelector(".topbar-shell");
if (navToggle && topbarShell) {
  navToggle.addEventListener("click", () => {
    const expanded = navToggle.getAttribute("aria-expanded") === "true";
    navToggle.setAttribute("aria-expanded", String(!expanded));
    topbarShell.classList.toggle("nav-open", !expanded);
  });
}

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll(".reveal").forEach((node, index) => {
    node.style.transitionDelay = `${Math.min(index * 70, 280)}ms`;
    observer.observe(node);
  });
} else {
  document.querySelectorAll(".reveal").forEach((node) => {
    node.classList.add("is-visible");
  });
}
