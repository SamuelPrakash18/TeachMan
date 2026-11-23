import { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { ReloadingScreen } from "./components/LoadingScreen";
import "./index.css";

function Root() {
  const [reloading, setReloading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setReloading(false), 850);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <>
      <ReloadingScreen visible={reloading} />
      <App />
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <BrowserRouter>
    <Root />
  </BrowserRouter>
);
