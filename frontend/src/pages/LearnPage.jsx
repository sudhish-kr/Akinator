import { useMemo, useState } from "react";
import { useI18n } from "../i18n/index.jsx";
import Mascot from "../components/Mascot.jsx";

const TYPE_OPTIONS = [
  { id: "real", labelKey: "learn.typeReal", categories: ["Sports", "Scientists", "Politicians", "Musicians", "Business Leaders", "Historical Figures"] },
  { id: "fictional", labelKey: "learn.typeFictional", categories: ["Movies", "TV Shows", "Anime", "Cartoons", "Gaming", "Literature", "Mythology"] },
  { id: "animal", labelKey: "learn.typeAnimal", categories: ["Cartoons", "Movies", "Mythology"] },
  { id: "other", labelKey: "learn.typeOther", categories: ["Sports", "Movies", "TV Shows", "Anime", "Cartoons", "Gaming", "Politics", "Science", "Music", "Literature", "Business Leaders"] },
];

const CATEGORY_LABELS = {
  Sports: "learn.catSports",
  Movies: "learn.catMovies",
  "TV Shows": "learn.catTv",
  Anime: "learn.catAnime",
  Cartoons: "learn.catCartoons",
  Gaming: "learn.catGaming",
  Politicians: "learn.catPolitics",
  Politics: "learn.catPolitics",
  Scientists: "learn.catScience",
  Science: "learn.catScience",
  Musicians: "learn.catMusic",
  Music: "learn.catMusic",
  Literature: "learn.catLiterature",
  "Business Leaders": "learn.catBusiness",
  "Historical Figures": "learn.catHistory",
  Mythology: "learn.catMythology",
};

/**
 * Wrong-guess wizard:
 * 1) type → 2) category → 3) suggestions → 4) manual type
 */
export default function LearnPage({
  wrongGuessName,
  characters,
  busy,
  onPick,
  onHome,
  onLoadSuggestions,
  onSearch,
}) {
  const { t } = useI18n();
  const [step, setStep] = useState("type"); // type | category | suggestions | manual
  const [kind, setKind] = useState(null);
  const [category, setCategory] = useState(null);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const typeMeta = useMemo(
    () => TYPE_OPTIONS.find((opt) => opt.id === kind) || null,
    [kind]
  );

  const pickType = async (opt) => {
    setKind(opt.id);
    setCategory(null);
    setStep("category");
  };

  const pickCategory = async (cat) => {
    setCategory(cat);
    setStep("suggestions");
    if (onLoadSuggestions) {
      await onLoadSuggestions(cat);
    }
  };

  const runSearch = async () => {
    if (!onSearch || !query.trim()) return;
    setSearching(true);
    try {
      await onSearch(query.trim(), category);
      setStep("suggestions");
    } finally {
      setSearching(false);
    }
  };

  return (
    <section className="page learn learn-stage">
      <div className="learn-mascot-wrap">
        <Mascot state="surprised" t={t} compact messageKey="mascot.wrong" />
      </div>
      <p className="kicker">{t("learn.kicker")}</p>
      <h2 className="title">{t("learn.title")}</h2>
      <p className="lede">
        {wrongGuessName
          ? t("learn.ledeWrong", { name: wrongGuessName })
          : t("learn.lede")}
      </p>

      {step === "type" && (
        <>
          <p className="muted">{t("learn.askType")}</p>
          <div className="char-grid">
            {TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                type="button"
                className="btn chip"
                disabled={busy}
                onClick={() => pickType(opt)}
              >
                {t(opt.labelKey)}
              </button>
            ))}
          </div>
        </>
      )}

      {step === "category" && typeMeta && (
        <>
          <p className="muted">{t("learn.askCategory")}</p>
          <div className="char-grid">
            {typeMeta.categories.map((cat) => (
              <button
                key={cat}
                type="button"
                className="btn chip"
                disabled={busy}
                onClick={() => pickCategory(cat)}
              >
                {t(CATEGORY_LABELS[cat] || "learn.catOther")}
              </button>
            ))}
          </div>
          <button type="button" className="btn ghost" disabled={busy} onClick={() => setStep("type")}>
            {t("learn.back")}
          </button>
        </>
      )}

      {step === "suggestions" && (
        <>
          <p className="muted">
            {category
              ? t("learn.askSuggestions", {
                  category: t(CATEGORY_LABELS[category] || "learn.catOther"),
                })
              : t("learn.askSuggestionsGeneric")}
          </p>
          <div className="char-grid">
            {characters.map((c) => (
              <button
                key={c.id}
                type="button"
                className="btn chip"
                disabled={busy}
                onClick={() => onPick(c.id, c.name)}
              >
                {c.name}
              </button>
            ))}
          </div>
          {!busy && characters.length === 0 && <p className="muted">{t("learn.empty")}</p>}
          <div className="actions">
            <button
              type="button"
              className="btn primary"
              disabled={busy}
              onClick={() => setStep("manual")}
            >
              {t("learn.typeName")}
            </button>
            <button
              type="button"
              className="btn ghost"
              disabled={busy}
              onClick={() => setStep("category")}
            >
              {t("learn.back")}
            </button>
          </div>
        </>
      )}

      {step === "manual" && (
        <>
          <p className="muted">{t("learn.askManual")}</p>
          <div className="learn-search">
            <input
              type="search"
              className="input"
              value={query}
              disabled={busy || searching}
              placeholder={t("learn.searchPlaceholder")}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") runSearch();
              }}
            />
            <button
              type="button"
              className="btn primary"
              disabled={busy || searching || !query.trim()}
              onClick={runSearch}
            >
              {t("learn.search")}
            </button>
          </div>
          <div className="char-grid">
            {characters.map((c) => (
              <button
                key={c.id}
                type="button"
                className="btn chip"
                disabled={busy}
                onClick={() => onPick(c.id, c.name)}
              >
                {c.name}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn ghost"
            disabled={busy}
            onClick={() => setStep("suggestions")}
          >
            {t("learn.back")}
          </button>
        </>
      )}

      <button type="button" className="btn ghost" disabled={busy} onClick={onHome}>
        {t("learn.home")}
      </button>
    </section>
  );
}
