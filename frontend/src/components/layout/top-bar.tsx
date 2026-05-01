import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ExternalLink, KeyRound, LogOut, UserCog } from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "./theme-toggle";
import { LanguageToggle } from "./language-toggle";
import { useAuth } from "@/hooks/useAuth";
import { ChangePasswordDialog } from "@/components/auth/change-password-dialog";

export function TopBar() {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const [pwdOpen, setPwdOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-4 px-4 sm:px-6">
        <NavLink to="/" className="flex items-center gap-2 font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <KeyRound className="h-4 w-4" />
          </div>
          <span className="text-sm sm:text-base">{t("common.appName")}</span>
          <span className="hidden text-xs font-normal text-muted-foreground sm:inline">
            · {t("common.tagline")}
          </span>
        </NavLink>

        <nav className="ml-4 hidden items-center gap-1 md:flex">
          <NavItem to="/" label={t("nav.dashboard")} end />
          <NavItem to="/keys" label={t("nav.keys")} />
          <NavItem to="/reports" label={t("nav.reports")} />
          <NavItem to="/config" label={t("nav.config")} />
        </nav>

        <div className="ml-auto flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="hidden sm:inline-flex"
            onClick={() => window.open("/api/docs", "_blank", "noopener,noreferrer")}
          >
            {t("nav.apiDocs")}
            <ExternalLink className="ml-1 h-3.5 w-3.5" />
          </Button>
          <LanguageToggle />
          <ThemeToggle />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="admin menu">
                <UserCog className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>admin</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setPwdOpen(true)}>
                <UserCog className="mr-2 h-4 w-4" />
                {t("nav.changePassword")}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={logout} className="text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                {t("nav.logout")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="border-t md:hidden">
        <div className="mx-auto flex max-w-[1600px] items-center gap-1 overflow-x-auto px-4 py-2">
          <NavItem to="/" label={t("nav.dashboard")} end />
          <NavItem to="/keys" label={t("nav.keys")} />
          <NavItem to="/reports" label={t("nav.reports")} />
          <NavItem to="/config" label={t("nav.config")} />
        </div>
      </div>

      <ChangePasswordDialog open={pwdOpen} onOpenChange={setPwdOpen} />
    </header>
  );
}

function NavItem({ to, label, end = false }: { to: string; label: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
          isActive
            ? "bg-secondary text-secondary-foreground"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
        )
      }
    >
      {label}
    </NavLink>
  );
}
