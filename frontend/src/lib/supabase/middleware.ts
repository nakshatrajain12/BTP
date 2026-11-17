import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh session — DO NOT remove this
  const { data: { user } } = await supabase.auth.getUser()
  
  const pathname = request.nextUrl.pathname;

  // Public paths — always allow 
  const isPublicPath = ['/login', '/signup', '/auth/callback'].some(p => pathname.startsWith(p));
  
  const isDev = process.env.NODE_ENV === 'development';
  const hasDummySession = request.cookies.get('dummy_session')?.value;
  const isAuthenticated = Boolean(user || hasDummySession);
  
  if (!isAuthenticated && !isPublicPath && !isDev) {
    // Not logged in and trying to access protected route → redirect to login
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  if (isAuthenticated && (pathname.startsWith('/login') || pathname.startsWith('/signup'))) {
    // Already logged in, redirect away from auth pages
    const url = request.nextUrl.clone()
    url.pathname = '/'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}
