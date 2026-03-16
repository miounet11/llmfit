const yearNodes = document.querySelectorAll(".year");
yearNodes.forEach((node) => {
  node.textContent = new Date().getFullYear();
});

const page = document.body.dataset.page;
if (page) {
  const activeLink = document.querySelector(`[data-page-link="${page}"]`);
  if (activeLink) {
    activeLink.classList.add("is-active");
  }
}

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
