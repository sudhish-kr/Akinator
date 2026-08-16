import { lazy, Suspense, useEffect, useState } from "react";
import GameApp from "./App.jsx";
import { I18nProvider } from "./i18n/index.jsx";
import "./styles.css";

const AdminApp = lazy(() => import("./admin/AdminApp.jsx"));

function getRoute() {
  const hash = window.location.hash.replace(/^#/, "") || "/";
  return hash.startsWith("/admin") ? "admin" : "game";
}

export default function Root() {
  const [route, setRoute] = useState(getRoute);

  useEffect(() => {
    const onHash = () => setRoute(getRoute());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <I18nProvider>
      {route === "admin" ? (
        <Suspense fallback={null}>
          <AdminApp />
        </Suspense>
      ) : (
        <GameApp />
      )}
    </I18nProvider>
  );
}
