"use client";

import { useEffect, useState, type FormEvent } from "react";
import type { AuthChangeEvent, Session } from "@supabase/supabase-js";

import { signIn, signOut, signUp } from "@/lib/supabase/auth";
import { createClient } from "@/lib/supabase/client";

type AuthMode = "signin" | "signup";

export default function Home() {
  const [mode, setMode] = useState<AuthMode>("signin");
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const supabase = createClient();
    let mounted = true;

    supabase.auth.getSession().then(
      ({ data: { session } }: { data: { session: Session | null } }) => {
        if (mounted) {
          setSession(session);
        }
      },
    );

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (_event: AuthChangeEvent, session: Session | null) => {
        setSession(session);
      },
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setNotice("");

    try {
      if (mode === "signin") {
        await signIn(email, password);
      } else {
        const { session } = await signUp(email, password);

        if (!session) {
          setNotice(
            "Your account has been created. Check your email for a confirmation link before signing in.",
          );
        } else {
          setNotice("Your account is ready. Welcome to LearnLoop!");
        }
      }

      setPassword("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleSignOut() {
    setLoading(true);
    setError("");

    try {
      await signOut();
      setNotice("You have signed out successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to sign out.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-5 py-12 text-white">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/10 bg-slate-900 shadow-2xl md:grid-cols-2">
        <section className="flex flex-col justify-between bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-800 p-9 md:p-12">
          <div>
            <div className="mb-12 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-xl font-black text-indigo-700">
                L
              </div>
              <span className="text-xl font-bold tracking-tight">
                LearnLoop
              </span>
            </div>

            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-indigo-100">
              Learn smarter. Grow faster.
            </p>

            <h1 className="max-w-md text-4xl font-bold leading-tight tracking-tight md:text-5xl">
              Your learning journey, built around you.
            </h1>

            <p className="mt-6 max-w-md text-base leading-7 text-indigo-100">
              LearnLoop adapts to your progress, identifies knowledge gaps,
              and helps you master concepts through personalized practice.
            </p>
          </div>

          <div className="mt-16 border-t border-white/20 pt-6">
            <p className="text-sm text-indigo-100">
              Personalized learning powered by adaptive intelligence.
            </p>
          </div>
        </section>

        <section className="p-8 md:p-12">
          {session ? (
            <div className="flex min-h-[420px] flex-col justify-center">
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-400/10 text-2xl text-emerald-400">
                ✓
              </div>

              <h2 className="text-3xl font-bold tracking-tight">
                You&apos;re signed in!
              </h2>

              <p className="mt-3 text-sm leading-6 text-slate-400">
                Welcome to LearnLoop. Your authenticated account is ready.
              </p>

              <div className="mt-8 rounded-xl border border-white/10 bg-slate-800 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                  Signed in as
                </p>
                <p className="mt-2 break-all text-sm text-white">
                  {session.user.email}
                </p>
              </div>

              <button
                type="button"
                onClick={handleSignOut}
                disabled={loading}
                className="mt-6 w-full rounded-xl border border-white/15 px-5 py-3 text-sm font-semibold transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Signing out..." : "Sign out"}
              </button>
            </div>
          ) : (
            <>
              <div className="mb-8">
                <h2 className="text-3xl font-bold tracking-tight">
                  {mode === "signin" ? "Welcome back" : "Create your account"}
                </h2>

                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {mode === "signin"
                    ? "Sign in to continue your personalized learning journey."
                    : "Join LearnLoop and start learning at your own pace."}
                </p>
              </div>

              <div className="mb-8 grid grid-cols-2 rounded-xl bg-slate-800 p-1">
                <button
                  type="button"
                  onClick={() => {
                    setMode("signin");
                    setError("");
                    setNotice("");
                  }}
                  className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
                    mode === "signin"
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Sign in
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setMode("signup");
                    setError("");
                    setNotice("");
                  }}
                  className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
                    mode === "signup"
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Create account
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label
                    htmlFor="email"
                    className="mb-2 block text-sm font-medium text-slate-300"
                  >
                    Email address
                  </label>

                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="mb-2 block text-sm font-medium text-slate-300"
                  >
                    Password
                  </label>

                  <input
                    id="password"
                    type="password"
                    autoComplete={
                      mode === "signin"
                        ? "current-password"
                        : "new-password"
                    }
                    required
                    minLength={6}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="At least 6 characters"
                    className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                {error && (
                  <p
                    role="alert"
                    className="rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-300"
                  >
                    {error}
                  </p>
                )}

                {notice && (
                  <p
                    role="status"
                    className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-300"
                  >
                    {notice}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-xl bg-indigo-600 px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-950/30 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading
                    ? "Please wait..."
                    : mode === "signin"
                      ? "Sign in to LearnLoop"
                      : "Create my account"}
                </button>
              </form>

              <p className="mt-8 text-center text-xs leading-5 text-slate-500">
                By continuing, you agree to use LearnLoop responsibly and
                protect your account credentials.
              </p>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
