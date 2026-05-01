import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { KeyRound, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LanguageToggle } from "@/components/layout/language-toggle";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { api, ApiError } from "@/lib/api";
import type { FirstRunResponse } from "@/types/api";

const schema = z.object({
  password: z.string().min(1, "required"),
});
type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { t } = useTranslation();
  const { login, isAuthenticated } = useAuth();
  const toast = useToast();
  const location = useLocation();
  const [isFirstRun, setIsFirstRun] = useState<boolean>(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { password: "" },
  });

  useEffect(() => {
    api
      .get<FirstRunResponse>("/api/settings/first-run", { skipAuth: true })
      .then((r) => setIsFirstRun(Boolean(r.is_first_run)))
      .catch(() => setIsFirstRun(false));
  }, []);

  if (isAuthenticated) {
    const from = (location.state as { from?: string } | null)?.from ?? "/";
    return <Navigate to={from} replace />;
  }

  const onSubmit = form.handleSubmit(async ({ password }) => {
    try {
      await login(password);
    } catch (err) {
      const message =
        err instanceof ApiError && err.status === 401
          ? t("auth.invalidPassword")
          : (err as Error).message;
      toast.error(t("auth.loginFailed"), message);
    }
  });

  return (
    <div className="relative flex min-h-full items-center justify-center overflow-hidden bg-gradient-to-br from-background via-background to-secondary px-4 py-12">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,theme(colors.primary/12),transparent_60%)]" />
      <div className="absolute right-4 top-4 flex items-center gap-1">
        <LanguageToggle />
        <ThemeToggle />
      </div>
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center sm:items-start sm:text-left">
          <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <KeyRound className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl">{t("auth.loginTitle")}</CardTitle>
          <CardDescription>{t("auth.loginSubtitle")}</CardDescription>
        </CardHeader>
        <form onSubmit={onSubmit}>
          <CardContent className="space-y-4">
            {isFirstRun && (
              <div className="rounded-md border border-dashed border-primary/40 bg-primary/5 p-3 text-sm text-primary">
                {t("auth.firstRunHint", { password: "kyx200328" })}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="password">{t("auth.password")}</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder={t("auth.passwordPlaceholder")}
                autoFocus
                {...form.register("password")}
              />
              {form.formState.errors.password ? (
                <p className="text-xs text-destructive">
                  {t("common.required")}
                </p>
              ) : null}
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : null}
              {t("auth.submit")}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
