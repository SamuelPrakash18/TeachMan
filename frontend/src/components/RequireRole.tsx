import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { getRole, getToken } from "../lib/api";

export default function RequireRole({
  role,
  children,
}: {
  role: string;
  children: ReactNode;
}) {
  if (!getToken() || getRole() !== role) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
