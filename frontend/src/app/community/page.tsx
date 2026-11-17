"use client";

import React, { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { MessageSquare, Users, ThumbsUp, Send, CheckCircle2, Mail } from "lucide-react";

function LinkedinIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect x="2" y="9" width="4" height="12" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  );
}

interface Post {
  id: string;
  author_name: string;
  company_name: string;
  category: string;
  title: string;
  content: string;
  upvotes: number;
  created_at: string;
}

interface Advisor {
  id: string;
  name: string;
  role_title: string;
  organization: string;
  expertise: string[];
  bio: string;
  linkedin_url?: string;
  contact_email?: string;
}

const DEFAULT_MOCK_POSTS: Post[] = [
  {
    id: "post-1",
    author_name: "Aarav Sharma",
    company_name: "Kavach Robotics",
    category: "Grants",
    title: "Timeline experience for SISFS disbursement through IIT Madras incubator",
    content: "Applied in December through IIT Madras Research Park. The committee review took 6 weeks, followed by a physical pitch. Received sanction letter for ₹30 Lakhs grant tranche last Tuesday.\n\nKey tip: Make sure your milestone projections have vendor quotes and test certificates attached—that significantly speeded up our approval without multiple back-and-forth queries!",
    upvotes: 28,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: "post-2",
    author_name: "Sneha Reddy",
    company_name: "BioSynthetix Labs",
    category: "Compliance",
    title: "Section 80-IAC Tax Exemption: Lessons from our recent CBDT approval",
    content: "We finally received our Inter-Ministerial Board (IMB) approval for 3 consecutive years of 100% tax holiday under Section 80-IAC!\n\nWhat worked: Ensure your DPIIT Certificate of Recognition has clear patent or technological innovation claims aligned with your MCA incorporation objects clause. Don't submit generic pitch decks—focus heavily on IP defensibility.",
    upvotes: 42,
    created_at: new Date(Date.now() - 86400000 * 4).toISOString(),
  },
  {
    id: "post-3",
    author_name: "Vikramaditya Bose",
    company_name: "CellShield Therapeutics",
    category: "Grants",
    title: "Applying for BIRAC BIG 26th Call – Peer review exchange?",
    content: "We are finalizing our grant proposal for the upcoming BIRAC Biotechnology Ignition Grant (₹50 Lakhs limit). Would love to connect with past grant recipients or fellow founders in therapeutics/diagnostics to peer-review technical PoC milestones and commercialization roadmaps.",
    upvotes: 19,
    created_at: new Date(Date.now() - 86400000 * 6).toISOString(),
  },
  {
    id: "post-4",
    author_name: "Rohan Mehta",
    company_name: "CloudScaleOps",
    category: "Investor Pitch",
    title: "Credit Guarantee Scheme for Startups (CGSS) vs CGTMSE – which is better for SaaS?",
    content: "Approaching partner banks for venture debt / collateral-free working capital. Has anyone here had experience getting CGSS guaranteed loans through SIDBI vs traditional CGTMSE through nationalized banks? What are the interest subventions like in practice?",
    upvotes: 15,
    created_at: new Date(Date.now() - 86400000 * 8).toISOString(),
  },
  {
    id: "post-5",
    author_name: "Divya Nair",
    company_name: "AgriVayu Tech",
    category: "DPIIT Recognition",
    title: "Quick Checklist: Step-by-step DPIIT Recognition in 48 hours (2026 Guide)",
    content: "Document checklist that got us approved in under 2 days:\n1. MCA Incorporation Certificate (< 10 yrs old)\n2. High-res product screenshot / prototype demo link\n3. 5-slide PDF explaining innovation, scalability, and job potential\n4. Verified CIN and registered GSTIN\n\nAvoid buzzwords without evidence—clearly explain what is technologically novel.",
    upvotes: 56,
    created_at: new Date(Date.now() - 86400000 * 11).toISOString(),
  },
  {
    id: "post-6",
    author_name: "Karan Johar",
    company_name: "NeuronEdge AI",
    category: "General",
    title: "IndiaAI Mission GPU compute cluster access – Anyone onboarded yet?",
    content: "Has anyone accessed the MeitY / IndiaAI GPU subsidies under the new 10,000 GPU initiative? We applied via the national AI portal for acoustic model training credits. Curious about the allocation timelines and cloud provider partners.",
    upvotes: 23,
    created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
  }
];

const DEFAULT_MOCK_ADVISORS: Advisor[] = [
  {
    id: "adv-1",
    name: "Dr. Ramesh Sundaram",
    role_title: "Senior Policy Consultant",
    organization: "Startup India Advisory Panel",
    expertise: ["DPIIT Section 80-IAC", "Seed Fund Scheme (SISFS)", "Tax Exemption"],
    bio: "Former advisor to DPIIT helping deep-tech and hardware startups navigate government seed funding, IMB clearances, and angel tax compliance.",
    linkedin_url: "https://linkedin.com",
    contact_email: "advisor@policyradar.in"
  },
  {
    id: "adv-2",
    name: "Priya Venkat",
    role_title: "Grant Specialist & Mentor",
    organization: "BioNEST / BIRAC Mentor Network",
    expertise: ["BIRAC BIG", "Biotech Grants", "Clinical Trials Compliance"],
    bio: "Assists early-stage life sciences, medtech, and biotech startups in structuring and writing winning BIRAC and DBT grant proposals.",
    linkedin_url: "https://linkedin.com",
    contact_email: "priya@policyradar.in"
  },
  {
    id: "adv-3",
    name: "Anand Kulkarni",
    role_title: "Legal & Regulatory Lead",
    organization: "Fintech Regulatory Sandbox",
    expertise: ["RBI Regulatory Sandbox", "FDI & Cross-Border", "ESOP Compliance"],
    bio: "Specializes in DPIIT compliances, cross-border payments, and regulatory sandbox applications for high-growth tech ventures.",
    linkedin_url: "https://linkedin.com",
    contact_email: "anand@policyradar.in"
  }
];

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState<"forum" | "advisors">("forum");
  const [posts, setPosts] = useState<Post[]>([]);
  const [advisors, setAdvisors] = useState<Advisor[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState("Grants");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const supabase = createClient();

  useEffect(() => {
    fetchPosts();
    fetchAdvisors();
  }, []);

  const fetchPosts = async () => {
    try {
      const { data } = await supabase
        .from("community_posts")
        .select("*")
        .order("created_at", { ascending: false });
      if (data && data.length > 0) {
        setPosts(data);
        return;
      }
    } catch (e) {
      console.warn("Could not fetch community_posts:", e);
    }
    setPosts(DEFAULT_MOCK_POSTS);
  };

  const fetchAdvisors = async () => {
    try {
      const { data } = await supabase.from("advisors").select("*");
      if (data && data.length > 0) {
        setAdvisors(data);
        return;
      }
    } catch (e) {
      console.warn("Could not fetch advisors:", e);
    }
    setAdvisors(DEFAULT_MOCK_ADVISORS);
  };

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    setIsSubmitting(true);
    let authorName = "Founder";
    let companyName = "My Startup";
    let authorId: string | undefined = undefined;

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        authorId = user.id;
        authorName = user.user_metadata?.full_name || user.email?.split("@")[0] || "Founder";
        companyName = user.user_metadata?.company_name || "Startup India";
      }
    } catch {}

    const newPostItem: Post = {
      id: `post-${Date.now()}`,
      author_name: authorName,
      company_name: companyName,
      category: newCategory,
      title: newTitle,
      content: newContent,
      upvotes: 0,
      created_at: new Date().toISOString(),
    };

    // Optimistically add to state
    setPosts((prev) => [newPostItem, ...prev]);

    try {
      if (authorId) {
        await supabase.from("community_posts").insert({
          author_id: authorId,
          author_name: authorName,
          company_name: companyName,
          category: newCategory,
          title: newTitle,
          content: newContent,
        });
      }
    } catch (err) {
      console.warn("Could not insert post to supabase:", err);
    }

    setIsSubmitting(false);
    setNewTitle("");
    setNewContent("");
  };

  const handleUpvote = async (postId: string, currentUpvotes: number) => {
    setPosts((prev) =>
      prev.map((p) => (p.id === postId ? { ...p, upvotes: (p.upvotes || 0) + 1 } : p))
    );
    try {
      await supabase
        .from("community_posts")
        .update({ upvotes: currentUpvotes + 1 })
        .eq("id", postId);
    } catch {}
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <a href="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-400 hover:text-blue-300 mb-3 transition-colors">
          &larr; Back to Dashboard
        </a>
        <h1 className="text-3xl font-bold tracking-tight text-white">Founder Community & Mentors</h1>
        <p className="text-slate-400 mt-1">Discuss scheme approvals, grant application advice, and connect with verified policy advisors.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700/60 mb-6 gap-6">
        <button
          onClick={() => setActiveTab("forum")}
          className={`flex items-center gap-2 pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "forum"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <MessageSquare className="w-4 h-4" /> Discussion Feed ({posts.length})
        </button>
        <button
          onClick={() => setActiveTab("advisors")}
          className={`flex items-center gap-2 pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "advisors"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Users className="w-4 h-4" /> Policy Advisors ({advisors.length})
        </button>
      </div>

      {/* Discussion Forum Tab */}
      {activeTab === "forum" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-4">
            {posts.length === 0 ? (
              <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl text-slate-400">
                No discussion threads yet. Be the first founder to post!
              </div>
            ) : (
              posts.map((post) => (
                <div
                  key={post.id}
                  style={{
                    background: "rgba(30, 41, 59, 0.45)",
                    backdropFilter: "blur(12px)",
                    borderRadius: 16,
                    padding: 20,
                    border: "1px solid rgba(255, 255, 255, 0.08)"
                  }}
                  className="shadow-sm hover:border-slate-600/80 transition-all"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold px-2.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">
                      {post.category}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(post.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white mb-2 leading-snug">{post.title}</h3>
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{post.content}</p>
                  <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-400">
                    <span>By <strong className="text-slate-200">{post.author_name}</strong> • {post.company_name}</span>
                    <button
                      onClick={() => handleUpvote(post.id, post.upvotes || 0)}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-blue-400 border border-slate-700/60 transition-colors cursor-pointer"
                    >
                      <ThumbsUp className="w-3.5 h-3.5 text-blue-400" /> {post.upvotes || 0}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* New Post Form */}
          <div
            style={{
              background: "rgba(30, 41, 59, 0.55)",
              backdropFilter: "blur(12px)",
              borderRadius: 16,
              padding: 20,
              border: "1px solid rgba(255, 255, 255, 0.08)"
            }}
            className="shadow-sm h-fit sticky top-6"
          >
            <h2 className="font-bold text-white mb-3 text-base">Ask or Share an Update</h2>
            <form onSubmit={handleCreatePost} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Topic Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full text-sm border border-slate-700 rounded-lg p-2.5 bg-slate-900 text-white focus:outline-blue-500 cursor-pointer"
                  style={{ backgroundColor: '#0f172a', color: '#ffffff', colorScheme: 'dark' }}
                >
                  <option value="Grants" style={{ backgroundColor: '#0f172a', color: '#ffffff' }}>Grants & Subsidies</option>
                  <option value="DPIIT Recognition" style={{ backgroundColor: '#0f172a', color: '#ffffff' }}>DPIIT Recognition</option>
                  <option value="Compliance" style={{ backgroundColor: '#0f172a', color: '#ffffff' }}>Compliance & Tax Exemption</option>
                  <option value="Investor Pitch" style={{ backgroundColor: '#0f172a', color: '#ffffff' }}>Investor Pitch</option>
                  <option value="General" style={{ backgroundColor: '#0f172a', color: '#ffffff' }}>General Discussion</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  placeholder="e.g. Has anyone received the SISFS seed grant approval in Tamil Nadu?"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full text-sm border border-slate-700 rounded-lg p-2.5 bg-slate-900 text-white placeholder:text-slate-500 focus:outline-blue-500"
                  style={{ backgroundColor: '#0f172a', color: '#ffffff', colorScheme: 'dark' }}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Details</label>
                <textarea
                  placeholder="Share details, questions, or timeline experiences..."
                  rows={4}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="w-full text-sm border border-slate-700 rounded-lg p-2.5 bg-slate-900 text-white placeholder:text-slate-500 focus:outline-blue-500"
                  style={{ backgroundColor: '#0f172a', color: '#ffffff', colorScheme: 'dark' }}
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-blue-600 text-white font-medium text-sm py-2.5 rounded-lg hover:bg-blue-500 transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 font-semibold"
              >
                <Send className="w-4 h-4" /> {isSubmitting ? "Posting..." : "Post to Community"}
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Advisor Directory Tab */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {advisors.map((advisor) => (
            <div
              key={advisor.id}
              style={{
                background: "rgba(30, 41, 59, 0.45)",
                backdropFilter: "blur(12px)",
                borderRadius: 16,
                padding: 20,
                border: "1px solid rgba(255, 255, 255, 0.08)"
              }}
              className="shadow-sm flex flex-col justify-between hover:border-slate-600/80 transition-all"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold text-white text-base">{advisor.name}</h3>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <p className="text-xs text-blue-400 font-medium">{advisor.role_title} • {advisor.organization}</p>
                <p className="text-xs text-slate-300 mt-3 leading-relaxed">{advisor.bio}</p>
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {advisor.expertise.map((tag, idx) => (
                    <span key={idx} className="text-[11px] bg-slate-800 text-slate-300 border border-slate-700/60 px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 mt-5 pt-3 border-t border-slate-700/50">
                {advisor.linkedin_url && (
                  <a href={advisor.linkedin_url} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-blue-400 transition-colors">
                    <LinkedinIcon className="w-4 h-4" />
                  </a>
                )}
                {advisor.contact_email && (
                  <a href={`mailto:${advisor.contact_email}`} className="text-slate-400 hover:text-blue-400 transition-colors">
                    <Mail className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
