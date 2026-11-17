'use server'

import { headers } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { Provider } from '@supabase/supabase-js'

export async function loginWithOAuth(provider: Provider) {
  const supabase = await createClient()
  const headersList = await headers()
  const host = headersList.get('host') || 'localhost:3000'
  const proto = headersList.get('x-forwarded-proto') || (host.includes('localhost') ? 'http' : 'https')
  const origin = process.env.NEXT_PUBLIC_SITE_URL || `${proto}://${host}`

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${origin}/auth/callback`,
    },
  })

  if (data?.url) {
    redirect(data.url)
  }
}

export async function login(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    return redirect(`/login?message=${encodeURIComponent(error.message)}`)
  }

  revalidatePath('/', 'layout')
  redirect('/')
}

export async function signup(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { data: authData, error } = await supabase.auth.signUp(data)

  if (error) {
    return redirect(`/signup?message=${encodeURIComponent(error.message)}`)
  }

  if (!authData.session) {
    return redirect('/login?message=Check your email to continue sign in process')
  }

  revalidatePath('/', 'layout')
  redirect('/')
}

export async function logout() {
  const supabase = await createClient()
  await supabase.auth.signOut()
  redirect('/login')
}
