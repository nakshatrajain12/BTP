'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';

export default function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string }>
}) {
  const params = React.use(searchParams);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(params.message || '');
  const router = useRouter();

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push('/');
    router.refresh();
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    setLoading(true);
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) {
      setError(error.message);
      setLoading(false);
    }
    // Will auto redirect if data.url exists
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden" style={{ backgroundColor: '#0a0d17', color: '#cbd5e1', fontFamily: '"Inter", sans-serif' }}>
      <div
        className="fixed inset-0 z-[-2]"
        style={{
          backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuC3cHhcT1XpjTAdTSMljXTOpg14NMqPr8j9F40sTj9ozfGSyHfosNZPUHoAxcLQoEYxaB9I0eopd4vyc2EWTEQNdgS34MdM9Qc1WsUAysSoDJEn8ouQ-HhoNXw6LrZTyil2SVhxynYPtwRjdZz1iEGp-9cNUTs5depFX2bPKnXuVve5xm_Ab5qJNRqEPYv3QfIiOB9zQcnOIZbAu9U4WNV8sKYOw6Hn1v4hpjSrKuHUL_cirhMGX7RWAiyEDHeB8XbFX5bntNdJzxo')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      ></div>
      <div className="absolute inset-0 z-[-1]" style={{ background: 'rgba(6,10,24,0.88)', backdropFilter: 'blur(40px)' }}></div>

      <div className="w-full max-w-md p-8 relative" style={{ background: 'rgba(30,41,59,0.5)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '24px' }}>
        <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full" style={{ background: 'rgba(59,130,246,0.2)', filter: 'blur(40px)' }}></div>
        <div className="absolute -bottom-10 -left-10 w-40 h-40 rounded-full" style={{ background: 'rgba(168,85,247,0.2)', filter: 'blur(40px)' }}></div>

        <div className="relative z-10 flex flex-col items-center mb-8">
          <div className="w-12 h-12 flex items-center justify-center mb-4" style={{ background: 'rgba(30,41,59,0.5)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <svg className="w-8 h-8" style={{ color: '#3b82f6' }} fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
              <path d="M4 4l16 16M4 20L20 4" strokeLinecap="round"></path>
            </svg>
          </div>
          <h1 style={{ fontSize: '30px', fontWeight: 900, color: '#fff', letterSpacing: '-0.05em', textTransform: 'uppercase', fontFamily: '"Manrope", sans-serif' }}>G.Take</h1>
          <p style={{ fontSize: '14px', color: '#94a3b8', marginTop: '8px' }}>Welcome back to Policy Intelligence</p>
        </div>

        <form className="relative z-10 flex flex-col gap-4" onSubmit={handleLogin}>
          <div className="flex flex-col gap-2">
            <label style={{ fontSize: '11px', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={{ borderRadius: '12px', padding: '12px 16px', background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(255,255,255,0.05)', outline: 'none', color: '#fff', fontSize: '14px' }}
            />
          </div>

          <div className="flex flex-col gap-2 mt-2">
            <label style={{ fontSize: '11px', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={{ borderRadius: '12px', padding: '12px 16px', background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(255,255,255,0.05)', outline: 'none', color: '#fff', fontSize: '14px' }}
            />
          </div>

          <div className="flex justify-end mt-1">
            <a href="#" style={{ fontSize: '12px', fontWeight: 700, color: '#60a5fa' }}>Forgot Password?</a>
          </div>

          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '12px', color: '#f87171', fontSize: '13px', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{ marginTop: '16px', background: loading ? '#1d4ed8' : '#2563eb', color: '#fff', padding: '14px 24px', borderRadius: '12px', fontWeight: 700, fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.05em', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', boxShadow: '0 0 20px rgba(37,99,235,0.3)', transition: 'all 0.2s' }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="flex items-center gap-2 mt-4">
            <span style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></span>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Or continue with</span>
            <span style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></span>
          </div>

          <div className="flex gap-4 mt-2">
            <button
              type="button"
              onClick={() => handleOAuth('google')}
              disabled={loading}
              style={{ flex: 1, background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.07)', color: '#fff', padding: '12px', borderRadius: '12px', fontWeight: 700, fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <img src="https://www.google.com/favicon.ico" className="w-4 h-4" alt="Google" />
              Google
            </button>
            <button
              type="button"
              onClick={() => handleOAuth('github')}
              disabled={loading}
              style={{ flex: 1, background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.07)', color: '#fff', padding: '12px', borderRadius: '12px', fontWeight: 700, fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <img src="https://github.com/favicon.ico" className="w-4 h-4" style={{ filter: 'invert(1)' }} alt="GitHub" />
              GitHub
            </button>
          </div>

          <p style={{ textAlign: 'center', fontSize: '14px', color: '#94a3b8', marginTop: '16px' }}>
            Don{"'"}t have an account?{' '}
            <a href="/signup" style={{ color: '#60a5fa', fontWeight: 700 }}>Sign up</a>
          </p>
        </form>
      </div>
    </div>
  );
}
