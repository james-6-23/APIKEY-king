import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import zhCN from "./zh-CN.json";
import en from "./en.json";

const LANG_KEY = "apikey-king:lang";

function initialLang(): string {
  try {
    const stored = localStorage.getItem(LANG_KEY);
    if (stored === "zh-CN" || stored === "en") return stored;
  } catch {
    // ignore
  }
  return "zh-CN";
}

void i18n.use(initReactI18next).init({
  resources: {
    "zh-CN": { translation: zhCN },
    en: { translation: en },
  },
  lng: initialLang(),
  fallbackLng: "zh-CN",
  interpolation: { escapeValue: false },
  returnNull: false,
});

i18n.on("languageChanged", (lng) => {
  try {
    localStorage.setItem(LANG_KEY, lng);
    document.documentElement.setAttribute("lang", lng);
  } catch {
    // ignore
  }
});

export default i18n;
