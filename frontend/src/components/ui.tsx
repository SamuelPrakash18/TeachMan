import {
  createContext,
  forwardRef,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

const controlClass =
  "w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-muted focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/30 disabled:cursor-not-allowed disabled:opacity-60";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-line bg-white p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

const buttonVariants: Record<ButtonVariant, string> = {
  primary: "bg-brand-green text-white hover:bg-brand-green/90",
  secondary: "bg-brand-blue text-white hover:bg-brand-blue/90",
  danger: "bg-danger text-white hover:bg-danger/90",
  ghost: "border border-line bg-white text-ink hover:bg-brand-cream",
};

export function Button({
  variant = "primary",
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${buttonVariants[variant]} ${className}`}
      {...rest}
    />
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-1.5 text-sm font-medium text-ink">
      <span>{label}</span>
      {children}
    </label>
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className = "", ...rest }, ref) {
    return <input ref={ref} className={`${controlClass} ${className}`} {...rest} />;
  },
);

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className = "", ...rest }, ref) {
    return <select ref={ref} className={`${controlClass} ${className}`} {...rest} />;
  },
);

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className = "", ...rest }, ref) {
    return <textarea ref={ref} className={`${controlClass} ${className}`} {...rest} />;
  },
);

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const toneClasses: Record<Tone, string> = {
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  info: "bg-brand-blue/10 text-brand-blue",
  neutral: "bg-line text-muted",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}

const statusTones: Record<string, Tone> = {
  paid: "success",
  verified: "success",
  approved: "success",
  conducted: "success",
  active: "success",
  partially_paid: "warning",
  pending: "warning",
  under_review: "warning",
  unpaid: "warning",
  paused: "warning",
  overdue: "danger",
  rejected: "danger",
  deactivated: "danger",
  issued: "info",
  requested: "info",
  scheduled: "info",
  cancelled: "neutral",
  draft: "neutral",
  closed: "neutral",
  ended: "neutral",
};

function statusLabel(status: string): string {
  const text = status.replace(/_/g, " ").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function StatusBadge({ status }: { status: string }) {
  const tone: Tone = statusTones[status.toLowerCase()] ?? "neutral";
  return <Badge tone={tone}>{statusLabel(status)}</Badge>;
}

export function Empty({
  title,
  text,
  children,
}: {
  title?: string;
  text?: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-dashed border-line bg-white p-8 text-center">
      {title && <h3 className="font-manrope text-base font-semibold text-ink">{title}</h3>}
      <p className="mt-1 text-sm text-muted">{text ?? children}</p>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-line ${className}`} />;
}

type StatTone = "default" | "success" | "warning" | "danger";

const statValueClasses: Record<StatTone, string> = {
  default: "text-ink",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

export function Stat({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: StatTone;
}) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className={`mt-1 font-manrope text-2xl font-bold ${statValueClasses[tone]}`}>
        {value}
      </p>
    </Card>
  );
}

export function Modal({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) {
      return;
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-ink/50" onClick={onClose} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-xl"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="font-manrope text-lg font-semibold text-ink">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md px-2 py-1 text-muted hover:bg-brand-cream hover:text-ink"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

type ToastTone = "success" | "error" | "info";

interface ToastItem {
  id: number;
  message: string;
  tone: ToastTone;
}

export type ToastFn = ((message: string, tone?: ToastTone) => void) & {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  toast: (message: string, tone?: ToastTone) => void;
};

function withToastMembers(send: (message: string, tone?: ToastTone) => void): ToastFn {
  return Object.assign(send, {
    success: (message: string) => send(message, "success"),
    error: (message: string) => send(message, "error"),
    info: (message: string) => send(message, "info"),
    toast: (message: string, tone?: ToastTone) => send(message, tone),
  });
}

const ToastContext = createContext<ToastFn | null>(null);

const toastClasses: Record<ToastTone, string> = {
  success: "bg-success text-white",
  error: "bg-danger text-white",
  info: "bg-brand-blue text-white",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const push = useCallback((message: string, tone: ToastTone = "info") => {
    nextId.current += 1;
    const id = nextId.current;
    setToasts((prev) => [...prev, { id, message, tone }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 3000);
  }, []);

  const api = useMemo(() => withToastMembers(push), [push]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        className="fixed bottom-4 right-4 z-[60] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2"
        aria-live="polite"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={`rounded-lg px-4 py-3 text-sm font-medium shadow-lg ${toastClasses[toast.tone]}`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastFn {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return withToastMembers(() => {});
  }
  return ctx;
}
