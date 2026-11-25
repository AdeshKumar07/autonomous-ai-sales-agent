import { RefreshCw, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { checkBackendHealth } from "../services/healthService";

function ConnectionStatus() {
  const [status, setStatus] = useState("checking"); // "online" | "offline" | "checking"

  const runHealthCheck = useCallback(async () => {
    try {
      await checkBackendHealth();
      setStatus("online");
    } catch {
      setStatus("offline");
    }
  }, []);

  const verifyConnection = useCallback(async () => {
    setStatus("checking");
    await runHealthCheck();
  }, [runHealthCheck]);

  useEffect(() => {
    let active = true;
    checkBackendHealth()
      .then(() => {
        if (active) setStatus("online");
      })
      .catch(() => {
        if (active) setStatus("offline");
      });
    return () => {
      active = false;
    };
  }, []);

  const isOnline = status === "online";
  const isChecking = status === "checking";

  return (
    <button
      type="button"
      onClick={verifyConnection}
      title="Click to re-check backend connection (http://127.0.0.1:8001/health)"
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
        isOnline
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/15"
          : isChecking
            ? "border-amber-500/30 bg-amber-500/10 text-amber-700"
            : "border-rose-500/30 bg-rose-500/10 text-rose-700 hover:bg-rose-500/15"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${
          isOnline
            ? "bg-emerald-500"
            : isChecking
              ? "bg-amber-500 animate-pulse"
              : "bg-rose-500"
        }`}
      />
      {isOnline ? (
        <Wifi className="h-3.5 w-3.5" />
      ) : isChecking ? (
        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <WifiOff className="h-3.5 w-3.5" />
      )}
      <span className="hidden sm:inline">
        {isOnline ? "Online" : isChecking ? "Checking..." : "Offline"}
      </span>
    </button>
  );
}

export default ConnectionStatus;
