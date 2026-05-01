import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { AuthProvider } from "@/hooks/useAuth";
import { ThemeProvider } from "@/hooks/useTheme";
import { ToastProvider } from "@/hooks/useToast";
import { TooltipProvider } from "@/components/ui/tooltip";

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <TooltipProvider delayDuration={200}>
            <RouterProvider router={router} />
          </TooltipProvider>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
