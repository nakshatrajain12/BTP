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
    const { data } = await supabase
      .from("community_posts")
      .select("*")
      .order("created_at", { ascending: false });
    if (data) setPosts(data);
  };

  const fetchAdvisors = async () => {
    const { data } = await supabase.from("advisors").select("*");
    if (data) setAdvisors(data);
  };

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    setIsSubmitting(true);
    const { data: { user } } = await supabase.auth.getUser();

    const { error } = await supabase.from("community_posts").insert({
      author_id: user?.id,
      author_name: user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Founder",
      company_name: user?.user_metadata?.company_name || "Startup India",
      category: newCategory,
      title: newTitle,
      content: newContent,
    });

    setIsSubmitting(false);
    if (!error) {
      setNewTitle("");
      setNewContent("");
      fetchPosts();
    }
  };

  const handleUpvote = async (postId: string, currentUpvotes: number) => {
    const { error } = await supabase
      .from("community_posts")
      .update({ upvotes: currentUpvotes + 1 })
      .eq("id", postId);

    if (!error) {
      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, upvotes: p.upvotes + 1 } : p))
      );
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <a href="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 mb-3 transition-colors">
          &larr; Back to Dashboard
        </a>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Founder Community & Mentors</h1>
        <p className="text-slate-500 mt-1">Discuss scheme approvals, grant application advice, and connect with verified policy advisors.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 mb-6 gap-6">
        <button
          onClick={() => setActiveTab("forum")}
          className={`flex items-center gap-2 pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "forum"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <MessageSquare className="w-4 h-4" /> Discussion Feed
        </button>
        <button
          onClick={() => setActiveTab("advisors")}
          className={`flex items-center gap-2 pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "advisors"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
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
              <div className="p-8 text-center bg-white border border-slate-200 rounded-xl text-slate-500">
                No discussion threads yet. Be the first founder to post!
              </div>
            ) : (
              posts.map((post) => (
                <div key={post.id} className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold px-2.5 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                      {post.category}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(post.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">{post.title}</h3>
                  <p className="text-sm text-slate-600 mt-2 whitespace-pre-line">{post.content}</p>
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>By {post.author_name} • {post.company_name}</span>
                    <button
                      onClick={() => handleUpvote(post.id, post.upvotes || 0)}
                      className="flex items-center gap-1.5 hover:text-blue-600 transition-colors cursor-pointer"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" /> {post.upvotes || 0}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* New Post Form */}
          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs h-fit sticky top-6">
            <h2 className="font-semibold text-slate-900 mb-3">Ask or Share an Update</h2>
            <form onSubmit={handleCreatePost} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Topic Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg p-2.5 bg-white focus:outline-blue-500"
                >
                  <option value="Grants">Grants & Subsidies</option>
                  <option value="DPIIT Recognition">DPIIT Recognition</option>
                  <option value="Compliance">Compliance & Tax Exemption</option>
                  <option value="Investor Pitch">Investor Pitch</option>
                  <option value="General">General Discussion</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  placeholder="e.g. Has anyone received the SISFS seed grant approval in Tamil Nadu?"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg p-2.5 focus:outline-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Details</label>
                <textarea
                  placeholder="Share details, questions, or timeline experiences..."
                  rows={4}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg p-2.5 focus:outline-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-blue-600 text-white font-medium text-sm py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
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
            <div key={advisor.id} className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold text-slate-900">{advisor.name}</h3>
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                </div>
                <p className="text-xs text-blue-600 font-medium">{advisor.role_title} • {advisor.organization}</p>
                <p className="text-xs text-slate-600 mt-3">{advisor.bio}</p>
                <div className="flex flex-wrap gap-1 mt-3">
                  {advisor.expertise.map((tag, idx) => (
                    <span key={idx} className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 mt-5 pt-3 border-t border-slate-100">
                {advisor.linkedin_url && (
                  <a href={advisor.linkedin_url} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-blue-600 transition-colors">
                    <LinkedinIcon className="w-4 h-4" />
                  </a>
                )}
                {advisor.contact_email && (
                  <a href={`mailto:${advisor.contact_email}`} className="text-slate-400 hover:text-blue-600 transition-colors">
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
