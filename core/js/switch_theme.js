const cssLink = document.getElementById('bootstrap-css');
const light = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css";
const dark = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap-dark.min.css";

function applyTheme() {
    const theme = localStorage.getItem("theme") || "light";
    cssLink.href = theme === "dark" ? dark : light;
}

function toggleTheme() {
    const current = localStorage.getItem("theme") || "light";
    const next = current === "light" ? "dark" : "light";
    localStorage.setItem("theme", next);
    applyTheme();
}

applyTheme();
