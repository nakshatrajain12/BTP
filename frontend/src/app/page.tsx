"use client";

import React, { useState, useEffect } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { useRouter } from "next/navigation";
import { Toaster, toast } from "sonner";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

// ─── Data Hooks ─────────────────────────────────────────
function useAPI<T>(url: string, opts?: RequestInit) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API}${url}`, opts)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  return { data, loading, error };
}

// ─── Types ────────────────────────────────────────────────
interface Scheme {
  id: string;
  scheme_name: string;
  ministry: string;
  funding_type: string;
  max_funding_amount: number;
  total_budget_allocated: number | null;
  startup_stage: string[];
  sector_eligibility: string[];
  geographic_restriction: string;
  application_portal: string;
  nlp_summary: string;
  status: string;
  category: string;
  dpiit_required: boolean;
}

interface Summary {
  total_schemes: number;
  total_budget: number;
  unique_ministries: number;
  avg_funding: number;
}

interface Alert {
  id: string;
  scheme_name: string;
  changed_fields: string[];
  changed_at: string;
}

// ─── Helper ───────────────────────────────────────────────
const fmtCurrency = (v: number | null) => {
  if (!v) return "₹0";
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(0)}K`;
  return `₹${v}`;
};

// ─── View Types ───────────────────────────────────────────
type View = "dashboard" | "schemes" | "analytics" | "alerts" | "stories";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [mounted, setMounted] = useState(false);
  const [userProfile, setUserProfile] = useState<{ startupName: string; sector: string } | null>(null);
  const router = useRouter();

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  useEffect(() => { 
    setMounted(true); 
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user?.user_metadata) {
        setUserProfile({
          startupName: user.user_metadata.startup_name || "Founder",
          sector: user.user_metadata.sector || "All Sectors"
        });
      }
    };
    getUser();
  }, [supabase]);

  if (!mounted) {
    return (
      <div style={{ backgroundColor: "#0a0d17", minHeight: "100vh" }}></div>
    );
  }

  const handleLogout = async () => {
    await supabase.auth.signOut();
    toast.success("Signed out successfully");
    setTimeout(() => { router.push("/login"); router.refresh(); }, 800);
  };

  return (
    <div style={{ backgroundColor: "#0a0d17", color: "#cbd5e1", minHeight: "100vh", fontFamily: '"Inter", sans-serif', display: "flex" }}>
      <Toaster richColors position="top-right" />
      
      {/* Background */}
      <div style={{
        position: "fixed", inset: 0, zIndex: -2,
        backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuC3cHhcT1XpjTAdTSMljXTOpg14NMqPr8j9F40sTj9ozfGSyHfosNZPUHoAxcLQoEYxaB9I0eopd4vyc2EWTEQNdgS34MdM9Qc1WsUAysSoDJEn8ouQ-HhoNXw6LrZTyil2SVhxynYPtwRjdZz1iEGp-9cNUTs5depFX2bPKnXuVve5xm_Ab5qJNRqEPYv3QfIiOB9zQcnOIZbAu9U4WNV8sKYOw6Hn1v4hpjSrKuHUL_cirhMGX7RWAiyEDHeB8XbFX5bntNdJzxo')",
        backgroundSize: "cover", backgroundPosition: "center"
      }} />
      <div style={{ position: "fixed", inset: 0, zIndex: -1, background: "rgba(6,10,24,0.9)", backdropFilter: "blur(40px)" }} />

      {/* Sidebar */}
      <aside style={{ width: 256, display: "flex", flexDirection: "column", justifyContent: "space-between", padding: "24px 8px", flexShrink: 0 }}>
        <div>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 16px 24px" }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="3"><path d="M4 4l16 16M4 20L20 4" strokeLinecap="round"/></svg>
            <span style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 20, color: "#fff", letterSpacing: "-0.05em" }}>G.Take</span>
          </div>
          
          {/* Nav */}
          <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {([
              { v: "dashboard",  icon: "dashboard",            label: "Dashboard" },
              { v: "schemes",    icon: "policy",               label: "Schemes Explorer" },
              { v: "analytics",  icon: "analytics",            label: "Analytics" },
              { v: "stories",    icon: "emoji_events",         label: "Success Stories" },
              { v: "alerts",     icon: "notifications_active", label: "Policy Alerts" },
            ] as { v: View, icon: string, label: string }[]).map(item => (
              <button
                key={item.v}
                onClick={() => setView(item.v)}
                style={{
                  width: "100%", display: "flex", alignItems: "center", gap: 14,
                  padding: "10px 16px", borderRadius: 12, border: "none", cursor: "pointer",
                  background: view === item.v ? "radial-gradient(circle at center, rgba(59,130,246,0.35) 0%, transparent 75%)" : "transparent",
                  color: view === item.v ? "#fff" : "#64748b",
                  fontWeight: view === item.v ? 700 : 500, fontSize: 14,
                  transition: "all 0.15s"
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 20, color: view === item.v ? "#60a5fa" : "inherit" }}>{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <button onClick={() => toast.info("Settings panel coming soon")} style={{ width: "100%", display: "flex", alignItems: "center", gap: 14, padding: "10px 16px", borderRadius: 12, border: "none", cursor: "pointer", background: "transparent", color: "#64748b", fontSize: 14, fontWeight: 500 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>settings</span>
            Settings
          </button>
          <button onClick={handleLogout} style={{ width: "100%", display: "flex", alignItems: "center", gap: 14, padding: "10px 16px", borderRadius: 12, border: "none", cursor: "pointer", background: "transparent", color: "#64748b", fontSize: 14, fontWeight: 500 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>logout</span>
            Log out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, padding: "24px 24px 24px 0", overflow: "auto" }}>
        {/* Header */}
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#475569" }}>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>home</span>
            <span>Home</span>
            <span>/</span>
            <span style={{ color: "#cbd5e1", fontWeight: 600 }}>
              {{ dashboard: "Dashboard", schemes: "Schemes Explorer", analytics: "Analytics", alerts: "Policy Alerts", stories: "Success Stories" }[view]}
            </span>
            {mounted && (
              <span style={{ marginLeft: 8, background: "rgba(30,41,59,0.5)", padding: "4px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.05)", color: "#cbd5e1" }}>
                {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button onClick={() => toast.info("Search coming soon")} style={{ width: 40, height: 40, borderRadius: "50%", background: "rgba(30,41,59,0.4)", border: "1px solid rgba(255,255,255,0.05)", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>search</span>
            </button>
            <button onClick={() => setView("alerts")} style={{ width: 40, height: 40, borderRadius: "50%", background: "rgba(30,41,59,0.4)", border: "1px solid rgba(255,255,255,0.05)", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>notifications</span>
              <span style={{ position: "absolute", top: 8, right: 8, width: 6, height: 6, background: "#3b82f6", borderRadius: "50%" }} />
            </button>
          </div>
        </header>

        {/* Views */}
        {view === "dashboard"  && <DashboardView onNavigate={setView} mounted={mounted} profile={userProfile} />}
        {view === "schemes"    && <SchemesView />}
        {view === "analytics"  && <AnalyticsView mounted={mounted} />}
        {view === "stories"    && <SuccessStoriesView />}
        {view === "alerts"     && <AlertsView mounted={mounted} />}
      </main>

      {/* Local Agent / Chatbot UI */}
      {mounted && <LocalAgentChatbot profile={userProfile} />}
    </div>
  );
}

// ══════════════════════════════════════════
// DASHBOARD VIEW
// ══════════════════════════════════════════
function DashboardView({ onNavigate, mounted, profile }: { onNavigate: (v: View) => void, mounted: boolean, profile: any }) {
  const { data: summary, loading: sLoading } = useAPI<Summary>("/analytics/summary");
  const { data: alertsData, loading: aLoading } = useAPI<{ alerts: Alert[] }>("/alerts/recent");
  const { data: fundingData } = useAPI<{ ministry: string; total_budget: number }[]>("/analytics/funding-by-ministry");
  const { data: recData, loading: rLoading } = useAPI<{ recommendations: any[] }>("/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      sector: profile?.sector || "Deeptech", 
      stage: "Idea", 
      state: "Pan-India" 
    })
  });

  const alerts = alertsData?.alerts || [];
  const recs = recData?.recommendations || [];
  const topAlert = alerts[0] || null;

  return (
    <div style={{ display: "flex", gap: 24 }}>
      {/* Main column */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Headline */}
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 38, color: "#fff", letterSpacing: "-0.03em", textTransform: "uppercase", margin: "0 0 8px" }}>
            Welcome, {profile?.startupName || "Founder"}!
          </h1>
          <p style={{ color: "#64748b", fontSize: 14, margin: 0 }}>AI-powered policies matching your <strong style={{ color: "#a855f7" }}>{profile?.sector || "curated"}</strong> profile</p>
        </div>

        {/* Stat cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 32 }}>
          <StatCard title="Total Schemes" value={sLoading ? "..." : String(summary?.total_schemes ?? 0)} sub="Active in database" icon="policy" color="#3b82f6" />
          <StatCard title="Total Budget Pool" value={sLoading ? "..." : fmtCurrency(summary?.total_budget ?? 0)} sub="Across all schemes" icon="payments" color="#22c55e" />
          <StatCard title="Ministries" value={sLoading ? "..." : String(summary?.unique_ministries ?? 0)} sub="Funding bodies" icon="account_balance" color="#a855f7" />
        </div>

        {/* Filter chips */}
        <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
          {["All Schemes", "Deeptech", "Agriculture", "Healthcare", "Fintech", "Idea Stage", "MVP Stage", "Scaling"].map((chip) => (
            <button key={chip} onClick={() => { onNavigate("schemes"); toast.success(`Filtering by: ${chip}`); }}
              style={{ padding: "6px 14px", borderRadius: 999, background: chip === "All Schemes" ? "rgba(59,130,246,0.2)" : "rgba(30,41,59,0.5)", border: chip === "All Schemes" ? "1px solid rgba(59,130,246,0.3)" : "1px solid rgba(255,255,255,0.05)", color: chip === "All Schemes" ? "#60a5fa" : "#94a3b8", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
              {chip}
            </button>
          ))}
        </div>

        {/* Scheme recommendations */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 800, fontSize: 18, color: "#fff", margin: 0 }}>AI Recommended Schemes</h2>
            <button onClick={() => onNavigate("schemes")} style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)", color: "#60a5fa", padding: "6px 14px", borderRadius: 999, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
              View All →
            </button>
          </div>

          {rLoading ? (
            <div style={{ padding: 32, textAlign: "center", color: "#475569" }}>Loading AI recommendations...</div>
          ) : recs.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {recs.map((rec: any, i: number) => (
                <SchemeCard key={i} scheme={rec} featured={i === 0} />
              ))}
            </div>
          ) : (
            <div style={{ padding: 32, textAlign: "center", color: "#475569", background: "rgba(30,41,59,0.3)", borderRadius: 16, border: "1px solid rgba(255,255,255,0.05)" }}>
              No AI recommendations available. Make sure the backend is running and try running the pipeline.
            </div>
          )}
        </div>
      </div>

      {/* Right sidebar */}
      <div style={{ width: 300, flexShrink: 0, display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Latest alert */}
        <div style={{ background: "linear-gradient(135deg, rgba(59,130,246,0.4) 0%, rgba(15,23,42,0.8) 100%)", borderRadius: 20, padding: 20, border: "1px solid rgba(255,255,255,0.08)", position: "relative", overflow: "hidden" }}>
          <div style={{ position: "absolute", top: -20, right: -20, width: 80, height: 80, background: "rgba(96,165,250,0.2)", borderRadius: "50%", filter: "blur(20px)" }} />
          <div style={{ position: "relative", zIndex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: 0 }}>Latest Alert</h3>
              <button onClick={() => onNavigate("alerts")} style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "50%", width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16, color: "#fff" }}>notifications_active</span>
              </button>
            </div>
            {aLoading ? (
              <p style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.6 }}>Loading alerts...</p>
            ) : topAlert ? (
              <>
                <p style={{ color: "#e2e8f0", fontSize: 13, lineHeight: 1.6, margin: "0 0 12px" }}>
                  <strong>{topAlert.scheme_name}</strong> updated: {topAlert.changed_fields?.join(", ")} changed.
                </p>
                <div style={{ fontSize: 11, color: "#93c5fd", fontWeight: 600 }}>
                  {mounted && new Date(topAlert.changed_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                </div>
              </>
            ) : (
              <p style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.6, margin: 0 }}>✅ No recent policy changes. You are up to date!</p>
            )}
          </div>
        </div>

        {/* Summary stats */}
        <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 20, padding: 20, border: "1px solid rgba(255,255,255,0.05)" }}>
          <h3 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 16px" }}>Platform Summary</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 24, color: "#fff" }}>{sLoading ? "..." : summary?.total_schemes}</div>
              <div style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginTop: 4 }}>Schemes</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 24, color: "#fff" }}>{sLoading ? "..." : fmtCurrency(summary?.avg_funding ?? 0)}</div>
              <div style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginTop: 4 }}>Avg Funding</div>
            </div>
          </div>
        </div>

        {/* Funding by ministry chart */}
        <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 20, padding: 20, border: "1px solid rgba(255,255,255,0.05)" }}>
          <h3 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 16px", textTransform: "uppercase", letterSpacing: "-0.02em" }}>Funding by Ministry</h3>
          {fundingData && fundingData.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {fundingData.slice(0, 6).map((item, i) => {
                const max = Math.max(...fundingData.map((f: any) => f.total_budget || 0));
                const pct = max > 0 ? ((item.total_budget || 0) / max) * 100 : 0;
                return (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#94a3b8", marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.ministry?.split(",")[0] || "Unknown"}</span>
                      <span style={{ fontWeight: 700, color: "#60a5fa" }}>{fmtCurrency(item.total_budget)}</span>
                    </div>
                    <div style={{ height: 4, borderRadius: 4, background: "rgba(30,41,59,0.8)" }}>
                      <div style={{ height: "100%", width: `${pct}%`, borderRadius: 4, background: "linear-gradient(90deg, #3b82f6, #60a5fa)" }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ color: "#475569", fontSize: 13, textAlign: "center", padding: 16 }}>Loading funding data...</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════
// SCHEMES EXPLORER VIEW
// ══════════════════════════════════════════
function SchemesView() {
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("");
  const [stage, setStage] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  
  const params = new URLSearchParams();
  if (sector) params.set("sector", sector);
  if (stage) params.set("stage", stage);
  if (category) params.set("category", category);
  params.set("page", String(page));
  params.set("limit", "12");

  const { data, loading } = useAPI<{ schemes: Scheme[] }>(`/schemes?${params.toString()}`);
  const [selected, setSelected] = useState<Scheme | null>(null);

  const schemes = (data?.schemes || []).filter(s =>
    !search || s.scheme_name.toLowerCase().includes(search.toLowerCase()) || s.ministry?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 28, color: "#fff", margin: 0, textTransform: "uppercase" }}>Schemes Explorer</h1>
        <span style={{ fontSize: 13, color: "#475569" }}>{schemes.length} schemes found</span>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search schemes or ministry..."
          style={{ flex: 1, minWidth: 200, padding: "10px 16px", borderRadius: 12, background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", color: "#fff", fontSize: 14, outline: "none" }}
        />
        <select value={sector} onChange={e => { setSector(e.target.value); setPage(1); }}
          style={{ padding: "10px 16px", borderRadius: 12, background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", color: "#94a3b8", fontSize: 13, cursor: "pointer" }}>
          <option value="">All Sectors</option>
          {["Technology", "Agriculture", "Healthcare", "Fintech", "Deeptech", "All Sectors", "Sector Agnostic"].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={stage} onChange={e => { setStage(e.target.value); setPage(1); }}
          style={{ padding: "10px 16px", borderRadius: 12, background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", color: "#94a3b8", fontSize: 13, cursor: "pointer" }}>
          <option value="">All Stages</option>
          {["Idea", "Prototype", "Early Revenue", "Scale-up"].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(1); }}
          style={{ padding: "10px 16px", borderRadius: 12, background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", color: "#94a3b8", fontSize: 13, cursor: "pointer" }}>
          <option value="">All Categories</option>
          {["Funding", "Incubation", "Tax Benefit", "Credit Support"].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Grid */}
      {loading ? (
        <div style={{ textAlign: "center", padding: 64, color: "#475569" }}>Loading schemes...</div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
            {schemes.map(scheme => (
              <SchemeDetailCard key={scheme.id} scheme={scheme} onClick={() => setSelected(scheme)} />
            ))}
          </div>
          {schemes.length === 0 && (
            <div style={{ textAlign: "center", padding: 64, color: "#475569" }}>No schemes found with these filters.</div>
          )}
          {/* Pagination */}
          <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 32 }}>
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)} style={{ padding: "8px 20px", borderRadius: 10, background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", color: "#94a3b8", cursor: page === 1 ? "not-allowed" : "pointer", opacity: page === 1 ? 0.4 : 1 }}>← Prev</button>
            <span style={{ padding: "8px 16px", color: "#475569", fontSize: 13 }}>Page {page}</span>
            <button disabled={(data?.schemes?.length ?? 0) < 12} onClick={() => setPage(p => p + 1)} style={{ padding: "8px 20px", borderRadius: 10, background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", color: "#94a3b8", cursor: "pointer" }}>Next →</button>
          </div>
        </>
      )}

      {/* Detail Modal */}
      {selected && <SchemeModal scheme={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

// ══════════════════════════════════════════
// SUCCESS STORIES VIEW
// ══════════════════════════════════════════
function SuccessStoriesView() {
  const { data, loading } = useAPI<{ stories: any[] }>("/success-stories");
  const stories = data?.stories || [];

  return (
    <div>
      <h1 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 28, color: "#fff", margin: "0 0 24px", textTransform: "uppercase" }}>Success Stories</h1>
      {loading ? (
        <div style={{ textAlign: "center", padding: 64, color: "#475569" }}>Loading stories...</div>
      ) : stories.length > 0 ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
          {stories.map(story => (
            <div key={story.id} style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 16, padding: 20, border: "1px solid rgba(255,255,255,0.05)" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: "#f59e0b", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>{story.ministry?.split(",")[0]}</div>
              <h3 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 12px" }}>{story.scheme_name}</h3>
              <p style={{ color: "#e2e8f0", fontSize: 13, lineHeight: 1.6, fontStyle: "italic", margin: "0 0 16px" }}>
                "{story.success_stories}"
              </p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 12 }}>
                {story.funding_type && <Tag label={story.funding_type} color="#3b82f6" />}
                {story.geographic_restriction && <Tag label={story.geographic_restriction} color="#a855f7" />}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 64, color: "#475569" }}>No success stories found.</div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════
// ANALYTICS VIEW
// ══════════════════════════════════════════
function AnalyticsView({ mounted }: { mounted: boolean }) {
  const { data, loading } = useAPI<any>("/analytics/detailed");
  
  if (loading) return <div style={{ padding: 64, textAlign: "center", color: "#475569" }}>Loading professional analytics module...</div>;
  if (!data) return <div style={{ padding: 64, textAlign: "center", color: "#475569" }}>Failed to load analytics data.</div>;

  const { summary, funding_by_ministry, sector_distribution, stage_coverage, funding_type_breakdown, state_vs_central } = data;
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6', '#f43f5e'];

  return (
    <div>
      <h1 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 28, color: "#fff", margin: "0 0 24px", textTransform: "uppercase" }}>Analytics Overview</h1>

      {/* KPI Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 32 }}>
        <StatCard title="Total Schemes" value={String(summary?.total_schemes ?? "...")} sub="Active Repository" icon="policy" color="#3b82f6" />
        <StatCard title="Total Budget Pool" value={fmtCurrency(summary?.total_budget ?? 0)} sub="Across tracked schemes" icon="paid" color="#22c55e" />
        <StatCard title="Avg Scheme Funding" value={fmtCurrency(summary?.avg_funding ?? 0)} sub="Per individual scheme" icon="trending_up" color="#f59e0b" />
        <StatCard title="Funding Bodies" value={String(summary?.unique_ministries ?? "...")} sub="Ministries/Departments" icon="account_balance" color="#8b5cf6" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
        {/* Budget by Ministry */}
        <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 20, padding: 24, border: "1px solid rgba(255,255,255,0.05)" }}>
          <h2 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 20px", textTransform: "uppercase", letterSpacing: "-0.02em" }}>Funding By Ministry</h2>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={(funding_by_ministry||[]).slice(0, 6)} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="ministry" type="category" width={140} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <RechartsTooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12, color: '#f8fafc' }} formatter={(val: number) => [fmtCurrency(val), "Budget"]} />
                <Bar dataKey="total_budget" radius={[0, 4, 4, 0]}>
                  {funding_by_ministry?.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Breakdown Analysis */}
        <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 20, padding: 24, border: "1px solid rgba(255,255,255,0.05)" }}>
          <h2 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 20px", textTransform: "uppercase", letterSpacing: "-0.02em" }}>Support Category Breakdown</h2>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={funding_type_breakdown || []} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="count" nameKey="category">
                  {funding_type_breakdown?.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12, color: '#f8fafc' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {/* Stage Coverage */}
        <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 20, padding: 24, border: "1px solid rgba(255,255,255,0.05)" }}>
          <h2 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 20px", textTransform: "uppercase", letterSpacing: "-0.02em" }}>Stage Focus</h2>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={stage_coverage || []} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="stage" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <RechartsTooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12, color: '#f8fafc' }} />
                <Bar dataKey="scheme_count" fill="#6366f1" radius={[8, 8, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sector Dominance */}
        <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 20, padding: 24, border: "1px solid rgba(255,255,255,0.05)", position: "relative", overflow: "hidden" }}>
          <h2 style={{ fontWeight: 700, fontSize: 16, color: "#fff", margin: "0 0 20px", textTransform: "uppercase", letterSpacing: "-0.02em" }}>Sector Dominance</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {(sector_distribution || []).slice(0, 7).map((item: any, i: number) => {
              const maxSector = Math.max(...(sector_distribution || []).map((s:any) => s.scheme_count));
              const pct = (item.scheme_count / maxSector) * 100;
              return (
                <div key={i} style={{ position: "relative", zIndex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, color: "#fff", textTransform: "uppercase", letterSpacing: "0.05em" }}>{item.sector}</span>
                    <span style={{ color: "#a78bfa", fontWeight: 800 }}>{item.scheme_count}</span>
                  </div>
                  <div style={{ height: 6, borderRadius: 8, background: "rgba(15,23,42,0.8)" }}>
                    <div style={{ height: "100%", width: `${pct}%`, borderRadius: 8, background: `linear-gradient(90deg, hsl(${260 + i * 15}, 70%, 50%), hsl(${280 + i * 15}, 80%, 65%))` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════
// ALERTS VIEW
// ══════════════════════════════════════════
function AlertsView({ mounted }: { mounted: boolean }) {
  const { data, loading } = useAPI<{ alerts: Alert[]; period_days: number }>("/alerts/recent?days=30");
  const alerts = data?.alerts || [];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 28, color: "#fff", margin: 0, textTransform: "uppercase" }}>Policy Alerts</h1>
        <span style={{ fontSize: 13, color: "#475569" }}>{alerts.length} updates in last 30 days</span>
      </div>
      {loading ? (
        <div style={{ textAlign: "center", padding: 64, color: "#475569" }}>Loading alerts...</div>
      ) : alerts.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {alerts.map((alert, i) => (
            <div key={alert.id || i} style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 16, padding: 20, border: "1px solid rgba(255,255,255,0.05)", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f59e0b", display: "inline-block" }} />
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#fbbf24" }}>Policy Update</span>
                </div>
                <h3 style={{ fontWeight: 700, fontSize: 15, color: "#fff", margin: "0 0 6px" }}>{alert.scheme_name}</h3>
                <p style={{ color: "#94a3b8", fontSize: 13, margin: 0 }}>
                  Fields changed: <strong style={{ color: "#e2e8f0" }}>{alert.changed_fields?.join(", ") || "General update"}</strong>
                </p>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 16 }}>
                <div style={{ fontSize: 12, color: "#475569", fontWeight: 600 }}>
                  {mounted && new Date(alert.changed_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                </div>
                <button onClick={() => toast.success("Alert dismissed")} style={{ marginTop: 8, padding: "4px 12px", borderRadius: 8, background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)", color: "#60a5fa", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 64, color: "#475569", background: "rgba(30,41,59,0.3)", borderRadius: 20, border: "1px solid rgba(255,255,255,0.05)" }}>
          <span className="material-symbols-outlined" style={{ fontSize: 48, marginBottom: 16, display: "block" }}>check_circle</span>
          No policy alerts in the last 30 days. You are fully up to date!
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════
// SUB-COMPONENTS
// ══════════════════════════════════════════
function StatCard({ title, value, sub, icon, color }: { title: string; value: string; sub: string; icon: string; color: string }) {
  return (
    <div style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 16, padding: 20, border: "1px solid rgba(255,255,255,0.05)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: `${color}22`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span className="material-symbols-outlined" style={{ fontSize: 18, color }}>{icon}</span>
        </div>
      </div>
      <div style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 26, color: "#fff", marginBottom: 4 }}>{value}</div>
      <div style={{ fontSize: 13, fontWeight: 700, color: "#fff", marginBottom: 2 }}>{title}</div>
      <div style={{ fontSize: 11, color: "#475569" }}>{sub}</div>
    </div>
  );
}

function SchemeCard({ scheme, featured }: { scheme: any, featured: boolean }) {
  return (
    <div style={{
      background: featured ? "linear-gradient(135deg, rgba(37,99,235,0.2) 0%, rgba(30,41,59,0.4) 100%)" : "rgba(30,41,59,0.4)",
      backdropFilter: "blur(12px)", borderRadius: 16, padding: 20, border: featured ? "1px solid rgba(59,130,246,0.2)" : "1px solid rgba(255,255,255,0.05)", position: "relative", overflow: "hidden"
    }}>
      {featured && <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: "linear-gradient(90deg, #2563eb, #60a5fa)" }} />}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {featured && <span style={{ fontSize: 10, fontWeight: 700, color: "#60a5fa", textTransform: "uppercase", letterSpacing: "0.1em", background: "rgba(59,130,246,0.1)", padding: "2px 8px", borderRadius: 999, border: "1px solid rgba(59,130,246,0.2)" }}>⭐ Top Match</span>}
        </div>
        <button onClick={() => window.open(scheme.application_url || "#", "_blank")} style={{ fontSize: 11, fontWeight: 700, color: "#60a5fa", background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)", padding: "4px 10px", borderRadius: 8, cursor: "pointer" }}>
          Apply →
        </button>
      </div>
      <h3 style={{ fontWeight: 700, fontSize: 15, color: "#fff", margin: "0 0 6px" }}>{scheme.name || scheme.scheme_name || "Scheme"}</h3>
      <p style={{ color: "#94a3b8", fontSize: 13, margin: "0 0 12px", lineHeight: 1.5 }}>{scheme.reason || "AI recommended based on your profile"}</p>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <Tag label="AI Recommended" color="#3b82f6" />
        {scheme.funding_type && <Tag label={scheme.funding_type} color="#22c55e" />}
      </div>
    </div>
  );
}

function SchemeDetailCard({ scheme, onClick }: { scheme: any, onClick: () => void }) {
  return (
    <div onClick={onClick} style={{ background: "rgba(30,41,59,0.4)", backdropFilter: "blur(12px)", borderRadius: 16, padding: 20, border: "1px solid rgba(255,255,255,0.05)", cursor: "pointer", transition: "border-color 0.15s, transform 0.15s", position: "relative" }}
      onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(59,130,246,0.3)"; (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)"; }}
      onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.05)"; (e.currentTarget as HTMLDivElement).style.transform = "none"; }}>
      
      {/* Updated Badge */}
      {scheme.recently_updated && (
        <span style={{ position: "absolute", top: -8, right: 16, fontSize: 10, fontWeight: 800, color: "#fbbf24", background: "rgba(251,191,36,0.2)", border: "1px solid rgba(251,191,36,0.4)", padding: "2px 8px", borderRadius: 999, zIndex: 10, backdropFilter: "blur(4px)" }}>
          🔄 UPDATED
        </span>
      )}

      {/* Info Button */}
      <button 
        onClick={(e) => { e.stopPropagation(); window.dispatchEvent(new CustomEvent('open-scheme-chat', { detail: scheme })); }}
        style={{ position: "absolute", bottom: 20, right: 20, width: 28, height: 28, borderRadius: "50%", background: "rgba(59,130,246,0.15)", border: "1px solid rgba(59,130,246,0.3)", color: "#60a5fa", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", transition: "all 0.2s" }}
        title="Chat about this scheme"
      >
        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>info</span>
      </button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: scheme.status === "Active" ? "#4ade80" : "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", background: scheme.status === "Active" ? "rgba(34,197,94,0.1)" : "rgba(30,41,59,0.5)", padding: "2px 8px", borderRadius: 999 }}>
          ● {scheme.status || "Active"}
        </span>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#60a5fa" }}>{fmtCurrency(scheme.max_funding_amount)}</span>
      </div>
      <h3 style={{ fontWeight: 700, fontSize: 14, color: "#fff", margin: "0 0 6px", lineHeight: 1.3 }}>{scheme.scheme_name}</h3>
      <p style={{ color: "#64748b", fontSize: 12, margin: "0 0 12px" }}>{scheme.ministry?.split(",")[0]}</p>
      <p style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.5, margin: "0 0 12px", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" as any }}>
        {scheme.nlp_summary}
      </p>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {scheme.funding_type && <Tag label={scheme.funding_type} color="#3b82f6" />}
        {scheme.geographic_restriction && <Tag label={scheme.geographic_restriction} color="#a855f7" />}
        {(scheme.startup_stage || []).slice(0, 2).map((s:string) => <Tag key={s} label={s} color="#f59e0b" />)}
      </div>
    </div>
  );
}

function SchemeModal({ scheme, onClose }: { scheme: Scheme, onClose: () => void }) {
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }} onClick={onClose}>
      <div style={{ background: "#0f172a", borderRadius: 24, padding: 32, maxWidth: 600, width: "90%", maxHeight: "85vh", overflowY: "auto", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 24px 64px rgba(0,0,0,0.5)" }} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "#4ade80", textTransform: "uppercase", background: "rgba(34,197,94,0.1)", padding: "3px 10px", borderRadius: 999 }}>● {scheme.status}</span>
          <button onClick={onClose} style={{ background: "rgba(30,41,59,0.5)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "50%", width: 32, height: 32, cursor: "pointer", color: "#94a3b8", display: "flex", alignItems: "center", justifyContent: "center" }}>✕</button>
        </div>
        <h2 style={{ fontFamily: '"Manrope",sans-serif', fontWeight: 900, fontSize: 22, color: "#fff", margin: "0 0 6px", lineHeight: 1.2 }}>{scheme.scheme_name}</h2>
        <p style={{ color: "#64748b", fontSize: 13, margin: "0 0 20px" }}>{scheme.ministry}</p>
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
          <InfoItem label="Max Funding" value={fmtCurrency(scheme.max_funding_amount)} />
          <InfoItem label="Funding Type" value={scheme.funding_type || "-"} />
          <InfoItem label="Geographic Scope" value={scheme.geographic_restriction || "Pan-India"} />
          <InfoItem label="DPIIT Required" value={scheme.dpiit_required ? "Yes" : "No"} />
          <InfoItem label="Category" value={scheme.category || "-"} />
          <InfoItem label="Launch Year" value={String((scheme as any).launch_year || "-")} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 11, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>About this Scheme</p>
          <p style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.7 }}>{scheme.nlp_summary || "No summary available."}</p>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
          {(scheme.startup_stage || []).map((s: string) => <Tag key={s} label={s} color="#f59e0b" />)}
          {(scheme.sector_eligibility || []).map((s: string) => <Tag key={s} label={s} color="#3b82f6" />)}
        </div>

        <a href={scheme.application_portal || "#"} target="_blank" rel="noopener noreferrer"
          style={{ display: "block", textAlign: "center", padding: "14px 24px", background: "#2563eb", color: "#fff", borderRadius: 12, fontWeight: 700, fontSize: 14, textDecoration: "none", boxShadow: "0 0 20px rgba(37,99,235,0.3)" }}>
          Apply for this Scheme →
        </a>
      </div>
    </div>
  );
}

function Tag({ label, color }: { label: string; color: string }) {
  return (
    <span style={{ fontSize: 10, fontWeight: 700, color, background: `${color}22`, border: `1px solid ${color}33`, padding: "2px 8px", borderRadius: 999, textTransform: "uppercase", letterSpacing: "0.05em" }}>
      {label}
    </span>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "rgba(15,23,42,0.4)", borderRadius: 10, padding: "10px 14px" }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#fff" }}>{value}</div>
    </div>
  );
}

// ══════════════════════════════════════════
// LOCAL AI GEMINI CHATBOT WIDGET
// ══════════════════════════════════════════
function LocalAgentChatbot({ profile }: { profile: any }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: "assistant" | "user", content: string }[]>([]);
  const [input, setInput] = useState("");
  const [schemeContext, setSchemeContext] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const handleOpenScheme = (e: any) => {
      setSchemeContext(e.detail);
      setOpen(true);
      setMessages([{ role: "assistant", content: `I have all the details for **${e.detail.scheme_name}**. What would you like to know about it?` }]);
    };
    window.addEventListener("open-scheme-chat", handleOpenScheme);
    return () => window.removeEventListener("open-scheme-chat", handleOpenScheme);
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const currentHistory = [...messages];
    const newMessages = [...currentHistory, { role: "user" as const, content: input }];
    setMessages(newMessages);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const endpoint = schemeContext ? "/chat/scheme" : "/chat";
      const body = schemeContext 
        ? { scheme_id: schemeContext.id, message: currentInput, history: currentHistory }
        : { message: currentInput, history: currentHistory };

      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.response || "Something went wrong." }]);
    } catch(err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Failed to reach the policy intelligence engine." }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (open && messages.length === 0 && !schemeContext) {
      setMessages([{ 
        role: "assistant", 
        content: `Hi ${profile?.startupName || "there"} team! I'm GOV-BOT. I've curated my policy intelligence around ${profile?.sector ? "the " + profile.sector + " sector" : "various schemes"}. How can I boost your funding trajectory today?` 
      }]);
    }
  }, [open, messages.length, profile, schemeContext]);

  return (
    <>
      <div 
        onClick={() => setOpen(!open)}
        style={{
          position: "fixed", bottom: 32, right: 32, width: 60, height: 60,
          background: "linear-gradient(135deg, #3b82f6, #93c5fd)", borderRadius: "50%",
          display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer",
          boxShadow: "0 10px 25px rgba(59,130,246,0.4), inset 0 -2px 5px rgba(0,0,0,0.2)",
          zIndex: 9999, transition: "transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)"
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.08)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 32, color: "#fff" }}>
          {open ? "close" : "smart_toy"}
        </span>
      </div>

      {open && (
        <div style={{
          position: "fixed", bottom: 110, right: 32, width: 360, height: 500,
          background: "rgba(15,23,42,0.85)", backdropFilter: "blur(20px)",
          borderRadius: 24, border: "1px solid rgba(59,130,246,0.3)",
          boxShadow: "0 24px 64px rgba(0,0,0,0.5)", zIndex: 9998,
          display: "flex", flexDirection: "column", overflow: "hidden",
          animation: "slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
        }}>
          {/* Header */}
          <div style={{ padding: "16px 20px", background: "rgba(30,41,59,0.9)", borderBottom: "1px solid rgba(255,255,255,0.05)", display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "linear-gradient(135deg, #3b82f6, #93c5fd)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 20, color: "#fff" }}>smart_toy</span>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 800, fontSize: 14, color: "#fff" }}>GOV-BOT</div>
              <div style={{ fontSize: 11, color: "#94a3b8", display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#4ade80" }} /> {schemeContext ? `Discussing: ${schemeContext.scheme_name.substring(0,20)}...` : "Startup Policy Intelligence"}
              </div>
            </div>
            {schemeContext && (
               <button onClick={() => { setSchemeContext(null); setMessages([]); }} style={{ background:"transparent", border:"none", color:"#fbbf24", cursor:"pointer", fontSize:11, fontWeight:700 }}>Clear Context</button>
            )}
          </div>

          {/* Messages */}
          <div style={{ flex: 1, padding: 20, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
            {messages.map((m, i) => (
              <div key={i} style={{ alignSelf: m.role === "user" ? "flex-end" : "flex-start", maxWidth: "80%" }}>
                <div style={{
                  background: m.role === "user" ? "#2563eb" : "rgba(30,41,59,0.8)",
                  padding: "12px 16px", borderRadius: m.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  fontSize: 13, lineHeight: 1.5, color: "#fff", border: m.role === "user" ? "none" : "1px solid rgba(255,255,255,0.1)",
                  whiteSpace: "pre-wrap"
                }}>
                  {m.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ alignSelf: "flex-start", maxWidth: "80%", background: "rgba(30,41,59,0.8)", padding: "12px 16px", borderRadius: "16px 16px 16px 4px", fontSize: 13, color: "#94a3b8", border: "1px solid rgba(255,255,255,0.1)" }}>
                Thinking...
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSend} style={{ padding: "16px 20px", background: "rgba(15,23,42,0.9)", borderTop: "1px solid rgba(255,255,255,0.05)", display: "flex", gap: 8 }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about grants, eligibility..."
              style={{ flex: 1, background: "rgba(30,41,59,0.8)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, padding: "10px 16px", color: "#fff", fontSize: 13, outline: "none" }}
            />
            <button type="submit" disabled={!input.trim()} style={{ background: "#3b82f6", border: "none", borderRadius: 12, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", cursor: input.trim() ? "pointer" : "not-allowed", opacity: input.trim() ? 1 : 0.5 }}>
              <span className="material-symbols-outlined" style={{ color: "#fff", fontSize: 20 }}>send</span>
            </button>
          </form>
        </div>
      )}
      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </>
  );
}
