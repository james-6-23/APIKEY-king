import { type ReactNode } from "react";
import { Navigate, Outlet, createBrowserRouter, useLocation } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { LoginPage } from "@/components/auth/login-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { ReportsPage } from "@/pages/reports-page";
import { ConfigPage } from "@/pages/config-page";
import { KeysPage } from "@/pages/keys-page";
import { useAuth } from "@/hooks/useAuth";

function Guard({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}

function ProtectedLayout() {
  return (
    <Guard>
      <AppShell>
        <Outlet />
      </AppShell>
    </Guard>
  );
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <ProtectedLayout />,
    children: [
      { path: "/", element: <DashboardPage /> },
      { path: "/keys", element: <KeysPage /> },
      { path: "/reports", element: <ReportsPage /> },
      { path: "/config", element: <ConfigPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
