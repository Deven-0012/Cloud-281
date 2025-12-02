import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  return (
    <div className="min-h-dvh bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="relative rounded-3xl border bg-white/80 backdrop-blur-xl shadow-[0_10px_30px_-12px_rgba(0,0,0,0.25)]">
          <div className="absolute -inset-[1px] rounded-3xl bg-gradient-to-tr from-gray-900/5 via-gray-900/0 to-gray-900/5 pointer-events-none" />

          <div className="relative p-8 md:p-10">
            <div className="mb-6">
              <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-gray-900 text-white font-bold">
                SC
              </div>
              <h1 className="mt-4 text-2xl font-semibold tracking-tight">
                Welcome back
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Sign in to continue to your dashboard.
              </p>
            </div>

            <form 
              className="space-y-5"
              onSubmit={async (e) => {
                e.preventDefault();
                setError("");
                setLoading(true);
                const result = await login(email, password);
                setLoading(false);
                if (result.success) {
                  navigate("/");
                } else {
                  setError(result.error || "Login failed");
                }
              }}
            >
              {error && (
                <div className="rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 outline-none focus:border-gray-900"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 pr-12 outline-none focus:border-gray-900"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    className="absolute inset-y-0 right-0 px-3 text-sm text-gray-600 hover:text-gray-900"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-gray-900 px-4 py-2.5 font-medium text-white transition hover:bg-black active:scale-[.99] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>

              <div className="flex items-center justify-between text-sm text-gray-600">
                <a
                  className="underline underline-offset-4 hover:no-underline"
                  href="#"
                >
                  Forgot password?
                </a>
                <span>
                  New here?{" "}
                  <Link
                    to="/register"
                    className="text-gray-900 underline underline-offset-4 hover:no-underline"
                  >
                    Create an account
                  </Link>
                </span>
              </div>
            </form>
          </div>
        </div>
        <p className="mt-6 text-center text-xs text-gray-500">
          By continuing you agree to our Terms & Privacy Policy.
        </p>
      </div>
    </div>
  );
}
