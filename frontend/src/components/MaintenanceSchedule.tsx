import { useEffect, useState, type FormEvent } from "react";
import { CalendarClock, Save } from "lucide-react";

import { api, type Maintenance, type MaintenanceSettings } from "../api";
import { useAsyncAction } from "../useAsyncAction";
import { ErrorBanner } from "./ErrorBanner";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const STATUS: Record<string, string> = {
  waiting: "waiting",
  running: "running",
  paused: "paused at the end of the window, continues next time",
  done: "done",
  stopped: "stopped",
  failed: "failed",
};

function settingsOf(m: Maintenance): MaintenanceSettings {
  const { next_window: _next, last_run: _last, ...s } = m;
  return s;
}

/** Server → Schedule: weekly TRIM and scrub while the cafe is closed. */
export function MaintenanceSchedule({ admin }: { admin: boolean }) {
  const { busy, error, setError, run } = useAsyncAction();
  const [saved, setSaved] = useState<Maintenance | null>(null);
  const [form, setForm] = useState<MaintenanceSettings | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    run("load", async () => {
      const m = await api.getSchedule();
      setSaved(m);
      setForm(settingsOf(m));
    });
  }, [run]);

  if (!form) return null;
  const set = (patch: Partial<MaintenanceSettings>) => {
    setDone(false);
    setForm({ ...form, ...patch });
  };

  async function save(e: FormEvent) {
    e.preventDefault();
    const ok = await run("save", async () => {
      const m = await api.saveSchedule(form!);
      setSaved(m);
      setForm(settingsOf(m));
    });
    if (ok) setDone(true);
  }

  const steps = [form.trim && "TRIM", form.scrub && "scrub"].filter(Boolean) as string[];
  const ordered = form.order === "trim_first" ? steps : [...steps].reverse();
  const last = saved?.last_run;
  return (
    <form className="card" onSubmit={save} aria-label="Schedule">
      <h3 className="card-title section-title">
        <CalendarClock size={15} /> Schedule
      </h3>
      <p className="muted small">
        Once a week, while the cafe is closed: the second job starts only when the first is done. A job still running
        when the window ends is paused and continues there the next week, so the PCs are never slowed down by day.
      </p>
      <ErrorBanner message={error} onClose={() => setError(null)} />
      <label className="check">
        <input
          type="checkbox"
          checked={form.enabled}
          onChange={(e) => set({ enabled: e.target.checked })}
          disabled={!admin}
        />
        Run TRIM and scrub on a schedule
      </label>
      <div className="form-row">
        <label>
          Day
          <select value={form.weekday} onChange={(e) => set({ weekday: Number(e.target.value) })} disabled={!admin}>
            {DAYS.map((d, i) => (
              <option key={d} value={i}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label>
          From
          <input
            type="time"
            value={form.start}
            onChange={(e) => set({ start: e.target.value })}
            required
            disabled={!admin}
          />
        </label>
        <label>
          Until
          <input type="time" value={form.end} onChange={(e) => set({ end: e.target.value })} required disabled={!admin} />
        </label>
        <label>
          Order
          <select
            value={form.order}
            onChange={(e) => set({ order: e.target.value as MaintenanceSettings["order"] })}
            disabled={!admin}
          >
            <option value="trim_first">TRIM, then scrub</option>
            <option value="scrub_first">Scrub, then TRIM</option>
          </select>
        </label>
      </div>
      <div className="form-row">
        <label className="check">
          <input type="checkbox" checked={form.trim} onChange={(e) => set({ trim: e.target.checked })} disabled={!admin} />
          TRIM
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={form.scrub}
            onChange={(e) => set({ scrub: e.target.checked })}
            disabled={!admin}
          />
          Scrub
        </label>
      </div>
      <p className="muted small">
        {form.enabled && ordered.length
          ? `Every ${DAYS[form.weekday]} ${form.start}–${form.end}${form.end <= form.start ? " (next morning)" : ""}: ${ordered.join(", then ")}.`
          : "Off: nothing runs on its own (Proxmox still scrubs the second Sunday of each month)."}
        {saved?.next_window && form.enabled && ` Next: ${new Date(saved.next_window).toLocaleString()}.`}
      </p>
      {last && (
        <p className="small">
          Last window {new Date(last.window_start).toLocaleString()}:{" "}
          {last.steps.map((s) => `${s.name === "trim" ? "TRIM" : "scrub"} ${STATUS[s.status] ?? s.status}`).join(", ")}
          {last.steps.some((s) => s.error) && (
            <span className="error-text"> ({last.steps.find((s) => s.error)!.error})</span>
          )}
        </p>
      )}
      {admin && (
        <button type="submit" disabled={busy !== null}>
          <Save size={14} /> {busy === "save" ? "Saving…" : done ? "Saved" : "Save schedule"}
        </button>
      )}
    </form>
  );
}
