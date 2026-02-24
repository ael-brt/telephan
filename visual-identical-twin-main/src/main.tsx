import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

function forceTelephanFavicon() {
  const href = "/telephan-tab-icon.svg?v=3";
  const head = document.head;
  if (!head) return;

  head
    .querySelectorAll('link[rel="icon"], link[rel="shortcut icon"], link[rel="alternate icon"]')
    .forEach((node) => node.parentNode?.removeChild(node));

  const icon = document.createElement("link");
  icon.rel = "icon";
  icon.type = "image/svg+xml";
  icon.href = href;
  head.appendChild(icon);

  const shortcut = document.createElement("link");
  shortcut.rel = "shortcut icon";
  shortcut.type = "image/svg+xml";
  shortcut.href = href;
  head.appendChild(shortcut);
}

forceTelephanFavicon();

createRoot(document.getElementById("root")!).render(<App />);
