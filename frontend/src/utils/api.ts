export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    // Read from local storage (set dynamically in Settings tab)
    const customUrl = localStorage.getItem("garuda_backend_url");
    if (customUrl) {
      return customUrl.replace(/\/$/, ""); // trim trailing slash
    }
  }
  
  // Build-time env fallback
  return (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
}
