import { ref, watchEffect } from "vue";

const theme = ref("light");

function init() {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") {
    theme.value = saved;
  } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    theme.value = "dark";
  }
}

init();

watchEffect(() => {
  document.documentElement.dataset.theme = theme.value;
  localStorage.setItem("theme", theme.value);
});

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === "light" ? "dark" : "light";
  }

  return { theme, toggleTheme };
}
