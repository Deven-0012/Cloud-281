import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const navigate = useNavigate();

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
                Create your account
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Join SmartCar to manage vehicles and telemetry.
              </p>
            </div>

            <form className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="name" className="block text-sm font-medium">
                  Full name
                </label>
                <input
                  id="name"
                  type="text"
                  placeholder="Leslie Alexander"
                  className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 outline-none focus:border-gray-900"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
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

              <div className="space-y-2">
                <label htmlFor="confirm" className="block text-sm font-medium">
                  Confirm password
                </label>
                <div className="relative">
                  <input
                    id="confirm"
                    type={showConfirm ? "text" : "password"}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 pr-12 outline-none focus:border-gray-900"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm((s) => !s)}
                    className="absolute inset-y-0 right-0 px-3 text-sm text-gray-600 hover:text-gray-900"
                  >
                    {showConfirm ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <button
                type="button"
                className="w-full rounded-xl bg-gray-900 px-4 py-2.5 font-medium text-white transition hover:bg-black active:scale-[.99]"
                onClick={() => navigate("/login")}
              >
                Create account
              </button>

              <p className="text-sm text-gray-600 text-center">
                Already have an account?{" "}
                <Link
                  to="/login"
                  className="text-gray-900 underline underline-offset-4 hover:no-underline"
                >
                  Sign in
                </Link>
              </p>
            </form>
          </div>
        </div>
        <p className="mt-6 text-center text-xs text-gray-500">
          Password must be at least 8 characters. Use a mix of letters and
          numbers.
        </p>
      </div>
    </div>
  );
}
