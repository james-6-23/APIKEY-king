import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useForm, type UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Save } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProxyManager } from "@/components/config/proxy-manager";
import { api, ApiError } from "@/lib/api";
import { normalizeProxyBlob } from "@/lib/proxies";
import { useToast } from "@/hooks/useToast";
import type { AppConfig, ConfigResponse } from "@/types/api";

const schema = z.object({
  github_tokens: z.string().transform((s) => s.trim()),
  proxy: z.string().optional(),
  scan_mode: z.enum([
    "compatible",
    "modelscope-only",
    "siliconflow-only",
    "deepseek-only",
  ]),
  date_range_days: z.coerce.number().int().min(1).max(3650),
  validators: z.object({
    modelscope: z.object({
      enabled: z.boolean(),
      model: z.string(),
    }),
    siliconflow: z.object({
      enabled: z.boolean(),
      model: z.string(),
    }),
    deepseek: z.object({
      enabled: z.boolean(),
    }),
  }),
  performance: z.object({
    max_concurrent_files: z.coerce.number().int().min(1).max(20),
    request_delay: z.coerce.number().min(0).max(10),
    github_timeout: z.coerce.number().int().min(10).max(120),
    validation_timeout: z.coerce.number().int().min(10).max(120),
    max_retries: z.coerce.number().int().min(0).max(10),
  }),
});

type FormValues = z.infer<typeof schema>;

const DEFAULTS: FormValues = {
  github_tokens: "",
  proxy: "",
  scan_mode: "compatible",
  date_range_days: 730,
  validators: {
    modelscope: { enabled: true, model: "Qwen/Qwen2-1.5B-Instruct" },
    siliconflow: { enabled: true, model: "Qwen/Qwen2.5-7B-Instruct" },
    deepseek: { enabled: true },
  },
  performance: {
    max_concurrent_files: 5,
    request_delay: 1,
    github_timeout: 30,
    validation_timeout: 30,
    max_retries: 3,
  },
};

function toFormValues(config: AppConfig | null): FormValues {
  if (!config) return DEFAULTS;
  const validators = config.validators ?? {};
  return {
    github_tokens: (config.github_tokens ?? []).join("\n"),
    proxy: config.proxy ?? "",
    scan_mode:
      (["compatible", "modelscope-only", "siliconflow-only", "deepseek-only"] as const).find(
        (m) => m === config.scan_mode,
      ) ?? "compatible",
    date_range_days: config.date_range_days ?? 730,
    validators: {
      modelscope: {
        enabled: validators.modelscope?.enabled ?? true,
        model: validators.modelscope?.model ?? "Qwen/Qwen2-1.5B-Instruct",
      },
      siliconflow: {
        enabled: validators.siliconflow?.enabled ?? true,
        model: validators.siliconflow?.model ?? "Qwen/Qwen2.5-7B-Instruct",
      },
      deepseek: {
        enabled: validators.deepseek?.enabled ?? true,
      },
    },
    performance: {
      max_concurrent_files: config.performance?.max_concurrent_files ?? 5,
      request_delay: config.performance?.request_delay ?? 1,
      github_timeout: config.performance?.github_timeout ?? 30,
      validation_timeout: config.performance?.validation_timeout ?? 30,
      max_retries: config.performance?.max_retries ?? 3,
    },
  };
}

function toPayload(values: FormValues) {
  const tokens = values.github_tokens
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  const proxyBlob = normalizeProxyBlob(values.proxy ?? "");
  return {
    github_tokens: tokens,
    proxy: proxyBlob || null,
    scan_mode: values.scan_mode,
    date_range_days: values.date_range_days,
    validators: {
      modelscope: values.validators.modelscope,
      siliconflow: values.validators.siliconflow,
      deepseek: { enabled: values.validators.deepseek.enabled, model: null },
    },
    performance: values.performance,
  };
}

export function ConfigPage() {
  const { t } = useTranslation();
  const toast = useToast();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULTS,
  });

  useEffect(() => {
    api
      .get<ConfigResponse>("/api/config")
      .then((res) => form.reset(toFormValues(res.config)))
      .catch((err) => toast.error(t("config.loadFailed"), (err as Error).message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = form.handleSubmit(async (values) => {
    const payload = toPayload(values);
    if (payload.github_tokens.length === 0) {
      toast.error(t("config.saveFailed"), t("config.tokensRequired"));
      return;
    }
    try {
      await api.post("/api/config", payload);
      toast.success(t("config.saveSuccess"));
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail ?? err.message : (err as Error).message;
      toast.error(t("config.saveFailed"), msg);
    }
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t("config.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("config.subtitle")}</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <Tabs defaultValue="credentials">
          <TabsList>
            <TabsTrigger value="credentials">{t("config.tabs.credentials")}</TabsTrigger>
            <TabsTrigger value="mode">{t("config.tabs.scanMode")}</TabsTrigger>
            <TabsTrigger value="validators">{t("config.tabs.validators")}</TabsTrigger>
            <TabsTrigger value="performance">{t("config.tabs.performance")}</TabsTrigger>
          </TabsList>

          <TabsContent value="credentials">
            <CredentialsTab form={form} />
          </TabsContent>
          <TabsContent value="mode">
            <ScanModeTab form={form} />
          </TabsContent>
          <TabsContent value="validators">
            <ValidatorsTab form={form} />
          </TabsContent>
          <TabsContent value="performance">
            <PerformanceTab form={form} />
          </TabsContent>
        </Tabs>

        <div className="flex justify-end">
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save />
            )}
            {t("common.save")}
          </Button>
        </div>
      </form>
    </div>
  );
}

type Form = UseFormReturn<FormValues>;

function CredentialsTab({ form }: { form: Form }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("config.tabs.credentials")}</CardTitle>
        <CardDescription>{t("config.credentials.githubTokensHint")}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2 md:col-span-2">
          <Label>{t("config.credentials.githubTokens")}</Label>
          <Textarea
            rows={6}
            placeholder={t("config.credentials.githubTokensPlaceholder")}
            className="mono text-xs"
            {...form.register("github_tokens")}
          />
          <p className="text-xs text-muted-foreground">
            {t("config.credentials.githubTokensHint")}
          </p>
        </div>
        <ProxyManager
          value={form.watch("proxy") ?? ""}
          onChange={(next) => form.setValue("proxy", next, { shouldDirty: true })}
        />
        <div className="space-y-2 md:col-span-2">
          <Label>{t("config.credentials.dateRange")}</Label>
          <Input type="number" min={1} max={3650} {...form.register("date_range_days")} />
          <p className="text-xs text-muted-foreground">{t("config.credentials.dateRangeHint")}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ScanModeTab({ form }: { form: Form }) {
  const { t } = useTranslation();
  const value = form.watch("scan_mode");
  const modes: { key: FormValues["scan_mode"]; label: string; desc: string }[] = [
    {
      key: "compatible",
      label: t("config.scanMode.compatible"),
      desc: t("config.scanMode.compatibleDesc"),
    },
    {
      key: "modelscope-only",
      label: t("config.scanMode.modelscope"),
      desc: t("config.scanMode.modelscopeDesc"),
    },
    {
      key: "siliconflow-only",
      label: t("config.scanMode.siliconflow"),
      desc: t("config.scanMode.siliconflowDesc"),
    },
    {
      key: "deepseek-only",
      label: t("config.scanMode.deepseek"),
      desc: t("config.scanMode.deepseekDesc"),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("config.scanMode.label")}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">
        {modes.map((m) => {
          const selected = value === m.key;
          return (
            <button
              key={m.key}
              type="button"
              onClick={() => form.setValue("scan_mode", m.key, { shouldDirty: true })}
              className={
                "relative flex flex-col items-start gap-1 rounded-lg border p-4 text-left transition " +
                (selected
                  ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                  : "hover:bg-accent/50")
              }
            >
              <span className="text-sm font-medium">{m.label}</span>
              <span className="text-xs text-muted-foreground">{m.desc}</span>
              {selected && (
                <span className="absolute right-3 top-3 h-2 w-2 rounded-full bg-primary" />
              )}
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}

function ValidatorsTab({ form }: { form: Form }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("config.tabs.validators")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <ValidatorRow
          title={t("config.validators.modelscope")}
          enabled={form.watch("validators.modelscope.enabled")}
          onEnabledChange={(v) =>
            form.setValue("validators.modelscope.enabled", v, { shouldDirty: true })
          }
          modelField={
            <Input
              className="mono text-xs"
              {...form.register("validators.modelscope.model")}
            />
          }
        />
        <ValidatorRow
          title={t("config.validators.siliconflow")}
          enabled={form.watch("validators.siliconflow.enabled")}
          onEnabledChange={(v) =>
            form.setValue("validators.siliconflow.enabled", v, { shouldDirty: true })
          }
          modelField={
            <Input
              className="mono text-xs"
              {...form.register("validators.siliconflow.model")}
            />
          }
        />
        <ValidatorRow
          title={t("config.validators.deepseek")}
          enabled={form.watch("validators.deepseek.enabled")}
          onEnabledChange={(v) =>
            form.setValue("validators.deepseek.enabled", v, { shouldDirty: true })
          }
          hint={t("config.validators.deepseekHint")}
        />
      </CardContent>
    </Card>
  );
}

function ValidatorRow({
  title,
  enabled,
  onEnabledChange,
  modelField,
  hint,
}: {
  title: string;
  enabled: boolean;
  onEnabledChange: (v: boolean) => void;
  modelField?: React.ReactNode;
  hint?: string;
}) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center">
      <div className="flex-1">
        <div className="text-sm font-medium">{title}</div>
        {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
      </div>
      <div className="flex items-center gap-2">
        <Label className="text-xs text-muted-foreground">
          {t("config.validators.enable")}
        </Label>
        <Switch checked={enabled} onCheckedChange={onEnabledChange} />
      </div>
      {modelField ? (
        <div className="min-w-[220px] space-y-1">
          <Label className="text-xs text-muted-foreground">
            {t("config.validators.model")}
          </Label>
          {modelField}
        </div>
      ) : null}
    </div>
  );
}

function PerformanceTab({ form }: { form: Form }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("config.tabs.performance")}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <NumberField
          label={t("config.performance.maxConcurrent")}
          hint={t("config.performance.maxConcurrentHint")}
          min={1}
          max={20}
          form={form}
          name="performance.max_concurrent_files"
        />
        <NumberField
          label={t("config.performance.requestDelay")}
          hint={t("config.performance.requestDelayHint")}
          min={0}
          max={10}
          step={0.1}
          form={form}
          name="performance.request_delay"
        />
        <NumberField
          label={t("config.performance.githubTimeout")}
          min={10}
          max={120}
          form={form}
          name="performance.github_timeout"
        />
        <NumberField
          label={t("config.performance.validationTimeout")}
          min={10}
          max={120}
          form={form}
          name="performance.validation_timeout"
        />
        <NumberField
          label={t("config.performance.maxRetries")}
          min={0}
          max={10}
          form={form}
          name="performance.max_retries"
        />
      </CardContent>
    </Card>
  );
}

function NumberField({
  label,
  hint,
  min,
  max,
  step,
  form,
  name,
}: {
  label: string;
  hint?: string;
  min?: number;
  max?: number;
  step?: number;
  form: Form;
  name:
    | "performance.max_concurrent_files"
    | "performance.request_delay"
    | "performance.github_timeout"
    | "performance.validation_timeout"
    | "performance.max_retries"
    | "date_range_days";
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input type="number" min={min} max={max} step={step} {...form.register(name)} />
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
