"use client";

import { useState, useEffect } from "react";
import { Settings, User, Key, Save, Check, Link2 } from "lucide-react";
import { getApiUrl } from "@/utils/api";

export default function SettingsPage() {
  const [isRegistered, setIsRegistered] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  // Profile settings
  const [fullName, setFullName] = useState("");
  const [deityPreference, setDeityPreference] = useState("Ganesha");
  const [philosophyPreference, setPhilosophyPreference] = useState("Advaita");
  const [goals, setGoals] = useState("");
  
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  
  // Backend URL configuration
  const [backendUrlInput, setBackendUrlInput] = useState("http://localhost:8000");

  useEffect(() => {
    // Check if token exists and fetch details
    const token = localStorage.getItem("token");
    if (token) {
      setIsRegistered(true);
      fetchProfile(token);
    }
    
    // Load custom backend URL from localStorage if any
    const savedBackend = localStorage.getItem("garuda_backend_url");
    if (savedBackend) {
      setBackendUrlInput(savedBackend);
    }
  }, []);

  const fetchProfile = async (token: string) => {
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/auth/me`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsername(data.username);
        setEmail(data.email);
        if (data.profile) {
          setFullName(data.profile.full_name || "");
          setDeityPreference(data.profile.deity_preference);
          setPhilosophyPreference(data.profile.philosophy_preference);
          setGoals(data.profile.spiritual_goals || "");
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          username,
          password,
          deity_preference: deityPreference,
          philosophy_preference: philosophyPreference
        })
      });

      if (res.ok) {
        // Automatically login
        handleLogin(e);
      } else {
        const errData = await res.json();
        setError(errData.detail || "Registration failed.");
      }
    } catch (err) {
      setError("Failed to connect to backend. Please check connection.");
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${getApiUrl()}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString()
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        setIsRegistered(true);
        setMessage("Logged in successfully!");
        fetchProfile(data.access_token);
      } else {
        setError("Invalid username or password.");
      }
    } catch (err) {
      setError("Failed to log in.");
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          full_name: fullName,
          deity_preference: deityPreference,
          philosophy_preference: philosophyPreference,
          spiritual_goals: goals
        })
      });

      if (res.ok) {
        setMessage("Spiritual profile saved successfully!");
        setTimeout(() => setMessage(""), 3000);
      } else {
        setError("Failed to save profile.");
      }
    } catch (err) {
      setError("Error saving profile details.");
    }
  };

  const handleSaveBackendUrl = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      // Validate basic format
      new URL(backendUrlInput);
      localStorage.setItem("garuda_backend_url", backendUrlInput);
      setMessage("Backend connection URL updated! Reloading parameters...");
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err) {
      setError("Please enter a valid URL (e.g. http://localhost:8000 or https://your-tunnel.ngrok-free.app)");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsRegistered(false);
    setUsername("");
    setPassword("");
    setEmail("");
    setFullName("");
    setMessage("Logged out successfully.");
  };

  return (
    <div className="space-y-6 max-w-2xl pb-10">
      {/* Title Header */}
      <div className="flex items-center gap-3">
        <Settings className="h-6 w-6 text-saffron saffron-glow" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Settings & Spiritual Profile</h2>
          <p className="text-xs text-muted-sacred">Configure your deity preferences, philosophical school, and manage your local user session</p>
        </div>
      </div>

      {message && (
        <div className="rounded-lg border border-emerald-950/40 bg-emerald-950/10 px-4 py-3 text-xs text-emerald-400">
          {message}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-950/40 bg-red-950/10 px-4 py-3 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Connection Settings panel */}
      <div className="rounded-xl border border-sacred-border bg-card p-6 space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground flex items-center gap-2">
          <Link2 className="h-4.5 w-4.5 text-saffron" />
          <span>Backend Connection Settings</span>
        </h3>
        <p className="text-[11px] text-muted-sacred leading-relaxed">
          Specify your local-first FastAPI backend service API base URL. Use <code className="text-saffron font-mono">http://localhost:8000</code> when running locally.
          If accessing via Vercel (HTTPS), enter a secure HTTPS tunnel URL (e.g. Cloudflare or ngrok) to prevent Mixed Content security blocks.
        </p>
        <form onSubmit={handleSaveBackendUrl} className="flex gap-2 items-end">
          <div className="flex-1 space-y-1">
            <label className="text-[9px] uppercase font-bold text-muted-sacred">Backend API URL</label>
            <input 
              type="text" 
              value={backendUrlInput}
              onChange={(e) => setBackendUrlInput(e.target.value)}
              placeholder="http://localhost:8000"
              className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/40 font-medium"
            />
          </div>
          <button
            type="submit"
            className="rounded bg-saffron text-background px-4 py-1.8 text-xs font-semibold hover:bg-saffron-light flex items-center gap-1 shrink-0 cursor-pointer"
          >
            <Save className="h-3.5 w-3.5" /> Save API URL
          </button>
        </form>
      </div>

      {/* Auth Panel if not registered */}
      {!isRegistered ? (
        <div className="rounded-xl border border-sacred-border bg-card p-6 space-y-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground flex items-center gap-2">
            <User className="h-4.5 w-4.5 text-saffron" />
            <span>Create Local Spiritual Session</span>
          </h3>

          <form className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-muted-sacred">Username</label>
                <input 
                  type="text" 
                  value={username} 
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. arjuna"
                  className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/40 font-medium"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-muted-sacred">Email address</label>
                <input 
                  type="email" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. arjuna@kurukshetra.org"
                  className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/40 font-medium"
                  required
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-muted-sacred">Password</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Secure local key"
                className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/40 font-medium"
                required
              />
            </div>

            <div className="flex gap-2.5 pt-2">
              <button 
                type="button"
                onClick={handleRegister} 
                className="rounded bg-saffron text-background px-4 py-2 text-xs font-semibold hover:bg-saffron-light cursor-pointer"
              >
                Register & Login
              </button>
              <button 
                type="button"
                onClick={handleLogin}
                className="rounded border border-sacred-border text-muted-sacred px-4 py-2 text-xs hover:bg-card-hover cursor-pointer"
              >
                Login Existing
              </button>
            </div>
          </form>
        </div>
      ) : (
        /* Profile Details Edit Form */
        <div className="rounded-xl border border-sacred-border bg-card p-6 space-y-6">
          <div className="flex justify-between items-center border-b border-sacred-border/60 pb-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
              Configure Spiritual Alignment
            </h3>
            <button 
              onClick={handleLogout}
              className="text-[10px] uppercase border border-red-900/40 text-red-400 bg-red-950/10 px-3 py-1 rounded hover:bg-red-950/30 cursor-pointer"
            >
              Logout Session
            </button>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-muted-sacred">Preferred Ishta Devata (Deity)</label>
                <select 
                  value={deityPreference} 
                  onChange={(e) => setDeityPreference(e.target.value)}
                  className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/30 font-medium"
                >
                  <option value="Ganesha">Lord Ganesha</option>
                  <option value="Shiva">Lord Shiva</option>
                  <option value="Krishna">Lord Krishna</option>
                  <option value="Devi">Divine Mother (Devi)</option>
                  <option value="Vishnu">Lord Vishnu</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-muted-sacred">Philosophical School</label>
                <select 
                  value={philosophyPreference} 
                  onChange={(e) => setPhilosophyPreference(e.target.value)}
                  className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/30 font-medium"
                >
                  <option value="Advaita">Advaita Vedanta (Non-Dualism)</option>
                  <option value="Vishishtadvaita">Vishishtadvaita (Qualified Non-Dualism)</option>
                  <option value="Dvaita">Dvaita Vedanta (Dualism)</option>
                  <option value="Yoga">Patanjali Raja Yoga</option>
                  <option value="Bhakti">Bhakti Marg (Devotion)</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-muted-sacred">Spiritual Goals / Vows</label>
              <textarea 
                value={goals} 
                onChange={(e) => setGoals(e.target.value)}
                placeholder="Write your core goals, practices, or vows here..."
                className="w-full h-24 rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron/30 font-medium"
              />
            </div>

            <button 
              type="submit"
              className="rounded bg-saffron text-background px-5 py-2 text-xs font-semibold hover:bg-saffron-light flex items-center gap-1.5 cursor-pointer saffron-glow"
            >
              <Save className="h-3.5 w-3.5" />
              <span>Save Configurations</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
