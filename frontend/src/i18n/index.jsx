import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { en } from "./locales/en.js";
import { hi } from "./locales/hi.js";
import { translateQuestion } from "./questions.js";

const STORAGE_KEY = "mg_lang";
const LOCALES = { en, hi };
export const SUPPORTED_LANGS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
];

const I18nContext = createContext(null);

function readStoredLang() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && LOCALES[stored]) return stored;
  } catch {
    /* ignore */
  }
  return "en";
}

function format(template, vars = {}) {
  return String(template ?? "").replace(/\{(\w+)\}/g, (_, key) =>
    vars[key] == null ? `{${key}}` : String(vars[key])
  );
}

function lookup(dict, path) {
  return path.split(".").reduce((node, key) => (node == null ? undefined : node[key]), dict);
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(readStoredLang);

  const setLang = useCallback((next) => {
    if (!LOCALES[next]) return;
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang === "hi" ? "hi" : "en";
  }, [lang]);

  const t = useCallback(
    (path, vars) => {
      const primary = lookup(LOCALES[lang], path);
      const fallback = lookup(en, path);
      const value = primary ?? fallback ?? path;
      return typeof value === "string" ? format(value, vars) : String(value);
    },
    [lang]
  );

  const tq = useCallback((sourceText) => translateQuestion(lang, sourceText), [lang]);

  const value = useMemo(() => ({ lang, setLang, t, tq }), [lang, setLang, t, tq]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}

export function LanguageSwitch({ className = "" }) {
  const { lang, setLang, t } = useI18n();
  return (
    <div className={`lang-switch ${className}`.trim()} role="group" aria-label={t("common.language")}>
      {SUPPORTED_LANGS.map((item) => (
        <button
          key={item.code}
          type="button"
          className={lang === item.code ? "active" : undefined}
          onClick={() => setLang(item.code)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
