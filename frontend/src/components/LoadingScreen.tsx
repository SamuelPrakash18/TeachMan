import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import Logo from "./Logo";

export function ReloadingScreen({ visible }: { visible: boolean }) {
  return (
    <div
      className={`fixed inset-0 z-[100] flex items-center justify-center bg-[#f7f9f5]/95 backdrop-blur-xl transition-opacity duration-300 ${
        visible ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
      }`}
      aria-hidden={!visible}
      aria-label={visible ? "Loading TeachMan" : undefined}
    >
      <div className="flex flex-col items-center">
        <div className="rounded-2xl border border-white/80 bg-white/80 px-6 py-4 shadow-[0_18px_60px_rgba(31,41,55,.16)] backdrop-blur-xl">
          <Logo size={38} />
        </div>
        <div className="mt-6 h-1 w-32 overflow-hidden rounded-full bg-brand-green/10">
          <div className="tm-loading-bar h-full rounded-full bg-brand-green" />
        </div>
      </div>
    </div>
  );
}

export function RouteLoadingBar() {
  const location = useLocation();
  const firstRender = useRef(true);
  const timer = useRef<number | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }

    setVisible(true);
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
    }
    timer.current = window.setTimeout(() => setVisible(false), 650);

    return () => {
      if (timer.current !== null) {
        window.clearTimeout(timer.current);
      }
    };
  }, [location.pathname, location.search]);

  return (
    <div
      className={`pointer-events-none fixed left-0 top-0 z-[90] h-[3px] w-full origin-left transition-opacity ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      {visible && <div className="tm-route-progress h-full rounded-r-full bg-brand-green" />}
    </div>
  );
}
