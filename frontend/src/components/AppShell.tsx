import { useState, type ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  Baby,
  BookOpen,
  Banknote,
  Bell,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Home,
  LayoutDashboard,
  LogOut,
  Menu,
  Receipt,
  Search,
  Settings,
  SlidersHorizontal,
  TrendingUp,
  UserPlus,
  Users,
  Wallet,
  X,
  type LucideIcon,
} from "lucide-react";
import { apiFetch, clearSession } from "../lib/api";
import Logo from "./Logo";

interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
}

const TUTOR_NAV: NavItem[] = [
  { label: "Dashboard", path: "/tutor", icon: LayoutDashboard },
  { label: "Students", path: "/tutor/students", icon: Users },
  { label: "Courses", path: "/tutor/courses", icon: BookOpen },
  { label: "Batches & Timetable", path: "/tutor/batches", icon: CalendarDays },
  { label: "Attendance", path: "/tutor/attendance", icon: ClipboardCheck },
  { label: "Enrollments", path: "/tutor/enrollments", icon: UserPlus },
  { label: "Fees & Invoices", path: "/tutor/invoices", icon: Receipt },
  { label: "Payments", path: "/tutor/payments", icon: Wallet },
  { label: "Expenses", path: "/tutor/expenses", icon: Banknote },
  { label: "Cash-Flow Forecast", path: "/tutor/forecast", icon: TrendingUp },
  { label: "What-If Simulator", path: "/tutor/simulator", icon: SlidersHorizontal },
  { label: "Notifications", path: "/tutor/notifications", icon: Bell },
  { label: "Settings", path: "/tutor/settings", icon: Settings },
];

const PARENT_NAV: NavItem[] = [
  { label: "Home", path: "/parent", icon: Home },
  { label: "Find Tutors", path: "/parent/find", icon: Search },
  { label: "My Children", path: "/parent/children", icon: Baby },
  { label: "My Classes", path: "/parent/classes", icon: BookOpen },
  { label: "Enrollment Requests", path: "/parent/enrollments", icon: UserPlus },
  { label: "Fees & Payments", path: "/parent/fees", icon: Receipt },
  { label: "Attendance", path: "/parent/attendance", icon: ClipboardCheck },
  { label: "Notifications", path: "/parent/notifications", icon: Bell },
  { label: "Profile", path: "/parent/settings", icon: Settings },
];

const linkBase =
  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition";

export default function AppShell({
  role,
  title = "Dashboard",
  children,
}: {
  role: "tutor" | "parent";
  title?: string;
  children: ReactNode;
}) {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const items = role === "tutor" ? TUTOR_NAV : PARENT_NAV;
  const basePath = `/${role}`;

  const closeDrawer = () => setDrawerOpen(false);

  async function handleLogout() {
    closeDrawer();
    try {
      await apiFetch("/account/logout", { method: "POST" });
    } catch {
      // Ignore errors: the local session is cleared regardless.
    }
    clearSession();
    navigate("/login", { replace: true });
  }

  function renderNav(compact: boolean, onNavigate?: () => void) {
    return (
      <nav className="flex-1 space-y-1 overflow-y-auto">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === basePath}
              title={item.label}
              onClick={onNavigate}
              className={({ isActive }) =>
                `${linkBase} ${compact ? "justify-center" : ""} ${
                  isActive ? "bg-brand-green text-white" : "text-ink hover:bg-brand-cream"
                }`
              }
            >
              <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
              {!compact && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    );
  }

  function renderFooter(compact: boolean, onNavigate?: () => void) {
    const footerClass = `${linkBase} text-ink hover:bg-brand-cream ${
      compact ? "justify-center" : ""
    }`;
    return (
      <div className="space-y-1 border-t border-line pt-3">
        <button
          type="button"
          title="Logout"
          onClick={handleLogout}
          className={`${footerClass} w-full`}
        >
          <LogOut className="h-5 w-5 shrink-0" aria-hidden="true" />
          {!compact && <span>Logout</span>}
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-cream text-ink">
      {/* Desktop sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-line bg-white p-3 md:flex ${
          collapsed ? "w-16" : "w-64"
        }`}
      >
        <div className="mb-4 flex items-center justify-between gap-2 px-1">
          <div className={collapsed ? "mx-auto" : ""}>
            <Logo size={32} showText={!collapsed} />
          </div>
          {!collapsed && (
            <button
              type="button"
              onClick={() => setCollapsed(true)}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
              className="rounded-md p-1 text-muted hover:bg-brand-cream hover:text-ink"
            >
              <ChevronLeft className="h-5 w-5" aria-hidden="true" />
            </button>
          )}
        </div>
        {collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(false)}
            aria-label="Expand sidebar"
            title="Expand sidebar"
            className="mb-3 self-center rounded-md p-1 text-muted hover:bg-brand-cream hover:text-ink"
          >
            <ChevronRight className="h-5 w-5" aria-hidden="true" />
          </button>
        )}
        {renderNav(collapsed)}
        {renderFooter(collapsed)}
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div
          className="fixed inset-0 z-40 bg-ink/40 md:hidden"
          onClick={closeDrawer}
          aria-hidden="true"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-white p-3 shadow-xl transition-transform duration-200 md:hidden ${
          drawerOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-hidden={!drawerOpen}
      >
        <div className="mb-4 flex items-center justify-between gap-2 px-1">
          <Logo size={32} />
          <button
            type="button"
            onClick={closeDrawer}
            aria-label="Close menu"
            className="rounded-md p-1 text-muted hover:bg-brand-cream hover:text-ink"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        {renderNav(false, closeDrawer)}
        {renderFooter(false, closeDrawer)}
      </aside>

      <div className={`transition-all ${collapsed ? "md:ml-16" : "md:ml-64"}`}>
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-line bg-white/95 px-4 py-3 backdrop-blur md:px-6">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
            className="rounded-lg p-2 text-ink hover:bg-brand-cream md:hidden"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <h1 className="font-manrope text-lg font-semibold text-ink">{title}</h1>
        </header>
        <main className="p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
