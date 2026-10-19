import { useState, type FormEvent } from "react";
import { KeyRound, LogIn, Server, UserPlus } from "lucide-react";

import { api, type User } from "../api";
import { useAsyncAction } from "../useAsyncAction";
import { ErrorBanner } from "./ErrorBanner";

interface Props {
  /** No user yet: the first admin is created with the setup code from the server. */
  setup: boolean;
  onSignedIn: (user: User) => void;
}

/** The sign-in screen, or the first-admin screen right after installing. */
export function SignIn({ setup, onSignedIn }: Props) {
  const { busy, error, setError, run } = useAsyncAction();
  const [code, setCode] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [again, setAgain] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (setup && password !== again) {
      setError("The passwords differ.");
      return;
    }
    await run("submit", async () => {
      const state = setup
        ? await api.setup(code.trim(), username.trim(), password)
        : await api.login(username.trim(), password);
      if (state.user) onSignedIn(state.user);
    });
  }

  return (
    <div className="signin-page">
      <form className="card signin-card" onSubmit={submit} aria-label={setup ? "Create the first admin" : "Sign in"}>
        <div className="signin-brand">
          <div className="brand-icon">
            <Server size={18} />
          </div>
          <span>ggNet</span>
        </div>
        <h2>{setup ? "Create the first admin" : "Sign in"}</h2>
        {setup && (
          <p className="muted small">
            Type the setup code the installer printed. On the server it is shown again by{" "}
            <code>ggnet-admin setup-code</code>.
          </p>
        )}
        <ErrorBanner message={error} onClose={() => setError(null)} />
        {setup && (
          <div className="form-group">
            <label htmlFor="signin-code">Setup code</label>
            <input
              id="signin-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. 3f9a-0c71-b2e4"
              autoComplete="off"
              required
              autoFocus
            />
          </div>
        )}
        <div className="form-group">
          <label htmlFor="signin-user">Username</label>
          <input
            id="signin-user"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            autoFocus={!setup}
          />
        </div>
        <div className="form-group">
          <label htmlFor="signin-password">Password</label>
          <input
            id="signin-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={setup ? "new-password" : "current-password"}
            minLength={setup ? 8 : undefined}
            required
          />
        </div>
        {setup && (
          <div className="form-group">
            <label htmlFor="signin-again">Password again</label>
            <input
              id="signin-again"
              type="password"
              value={again}
              onChange={(e) => setAgain(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
        )}
        <button type="submit" className="btn-primary" disabled={busy !== null}>
          {setup ? <UserPlus size={15} /> : <LogIn size={15} />}
          {busy ? "Please wait…" : setup ? "Create admin" : "Sign in"}
        </button>
        {!setup && (
          <p className="muted small signin-hint">
            <KeyRound size={12} /> Forgot the password? An admin resets it in Settings → Users, or on the server:{" "}
            <code>ggnet-admin reset-password NAME</code>.
          </p>
        )}
      </form>
    </div>
  );
}
