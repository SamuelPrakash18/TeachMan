import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import RequireRole from "./components/RequireRole";
import { ToastProvider } from "./components/ui";
import AnalyticsChatBubble from "./components/AnalyticsChatBubble";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import TutorRegister from "./pages/TutorRegister";
import ParentRegister from "./pages/ParentRegister";
import Notifications from "./pages/Notifications";
import TutorDashboard from "./pages/tutor/Dashboard";
import TutorStudents from "./pages/tutor/Students";
import TutorCourses from "./pages/tutor/Courses";
import TutorBatches from "./pages/tutor/Batches";
import TutorAttendance from "./pages/tutor/Attendance";
import TutorEnrollments from "./pages/tutor/Enrollments";
import TutorInvoices from "./pages/tutor/Invoices";
import TutorPayments from "./pages/tutor/Payments";
import TutorExpenses from "./pages/tutor/Expenses";
import TutorForecast from "./pages/tutor/Forecast";
import TutorSimulator from "./pages/tutor/Simulator";
import TutorLearning from "./pages/tutor/Learning";
import TutorSettings from "./pages/tutor/Settings";
import ParentHome from "./pages/parent/Home";
import ParentFindTutors from "./pages/parent/FindTutors";
import ParentChildren from "./pages/parent/Children";
import ParentClasses from "./pages/parent/Classes";
import ParentEnrollments from "./pages/parent/Enrollments";
import ParentFees from "./pages/parent/Fees";
import ParentAttendance from "./pages/parent/Attendance";
import ParentLearning from "./pages/parent/Learning";
import ParentSettings from "./pages/parent/Settings";

function ShellLayout({ role, title }: { role: "tutor" | "parent"; title?: string }) {
  return (
    <AppShell role={role} title={title}>
      <Outlet />
      {role === "tutor" && <AnalyticsChatBubble />}
    </AppShell>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register/tutor" element={<TutorRegister />} />
        <Route path="/register/parent" element={<ParentRegister />} />

        <Route
          path="/tutor"
          element={
            <RequireRole role="tutor">
              <ShellLayout role="tutor" />
            </RequireRole>
          }
        >
          <Route index element={<TutorDashboard />} />
          <Route path="students" element={<TutorStudents />} />
          <Route path="courses" element={<TutorCourses />} />
          <Route path="batches" element={<TutorBatches />} />
          <Route path="attendance" element={<TutorAttendance />} />
          <Route path="enrollments" element={<TutorEnrollments />} />
          <Route path="invoices" element={<TutorInvoices />} />
          <Route path="payments" element={<TutorPayments />} />
          <Route path="expenses" element={<TutorExpenses />} />
          <Route path="forecast" element={<TutorForecast />} />
          <Route path="simulator" element={<TutorSimulator />} />
          <Route path="learning" element={<TutorLearning />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="settings" element={<TutorSettings />} />
        </Route>

        <Route
          path="/parent"
          element={
            <RequireRole role="parent">
              <ShellLayout role="parent" />
            </RequireRole>
          }
        >
          <Route index element={<ParentHome />} />
          <Route path="find" element={<ParentFindTutors />} />
          <Route path="children" element={<ParentChildren />} />
          <Route path="classes" element={<ParentClasses />} />
          <Route path="enrollments" element={<ParentEnrollments />} />
          <Route path="fees" element={<ParentFees />} />
          <Route path="attendance" element={<ParentAttendance />} />
          <Route path="learning" element={<ParentLearning />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="settings" element={<ParentSettings />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ToastProvider>
  );
}
