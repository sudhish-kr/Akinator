import { useI18n } from "../i18n/index.jsx";

export default function HomePage({ onStart, busy }) {
  const { t } = useI18n();
  return (
    <section className="page home">
      <p className="kicker">{t("home.kicker")}</p>
      <h1 className="brand">
        Mind<span>Guess</span>
      </h1>
      <p className="lede">{t("home.lede")}</p>
      <button type="button" className="btn primary lg" onClick={onStart} disabled={busy}>
        {busy ? t("home.connecting") : t("home.start")}
      </button>
      <a className="admin-entry" href="#/admin">
        {t("home.admin")}
      </a>
    </section>
  );
}
