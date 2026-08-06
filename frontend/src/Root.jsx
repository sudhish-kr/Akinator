import { useEffect, useState } from "react";
import GameApp from "./App.jsx";
import AdminApp from "./admin/AdminApp.jsx";
import "./styles.css";
import "./admin/admin.css";

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

  return route === "admin" ? <AdminApp /> : <GameApp />;
}
