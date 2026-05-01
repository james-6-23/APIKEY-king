import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";

function buildSchema(t: (k: string) => string) {
  return z
    .object({
      old_password: z.string().min(1, t("common.required")),
      new_password: z.string().min(6, t("auth.passwordMin")),
      confirm: z.string().min(6, t("auth.passwordMin")),
    })
    .refine((v) => v.new_password === v.confirm, {
      message: t("auth.passwordMismatch"),
      path: ["confirm"],
    });
}

type FormValues = z.infer<ReturnType<typeof buildSchema>>;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChangePasswordDialog({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const toast = useToast();
  const { logout } = useAuth();
  const schema = buildSchema(t);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { old_password: "", new_password: "", confirm: "" },
  });

  useEffect(() => {
    if (!open) form.reset({ old_password: "", new_password: "", confirm: "" });
  }, [open, form]);

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await api.post("/api/settings/change-password", {
        old_password: values.old_password,
        new_password: values.new_password,
      });
      toast.success(t("auth.changePasswordSuccess"));
      onOpenChange(false);
      logout();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.detail ?? err.message
          : (err as Error).message;
      toast.error(t("auth.changePasswordFailed"), msg);
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("auth.changePasswordTitle")}</DialogTitle>
          <DialogDescription>{t("auth.loginSubtitle")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="old_password">{t("auth.oldPassword")}</Label>
            <Input id="old_password" type="password" {...form.register("old_password")} />
            {form.formState.errors.old_password ? (
              <p className="text-xs text-destructive">
                {form.formState.errors.old_password.message}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="new_password">{t("auth.newPassword")}</Label>
            <Input id="new_password" type="password" {...form.register("new_password")} />
            {form.formState.errors.new_password ? (
              <p className="text-xs text-destructive">
                {form.formState.errors.new_password.message}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">{t("auth.confirmPassword")}</Label>
            <Input id="confirm" type="password" {...form.register("confirm")} />
            {form.formState.errors.confirm ? (
              <p className="text-xs text-destructive">
                {form.formState.errors.confirm.message}
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : null}
              {t("common.submit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
