import React from "react";
import ReactDOM from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import Root from "./Root.jsx";

// Register after the page has loaded so the service worker does not compete
// with the first Start Game click (it does not cache the Render API).
registerSW();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
