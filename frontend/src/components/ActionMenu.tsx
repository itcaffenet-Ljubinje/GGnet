import { useEffect, useRef, useState } from "react";
import { MoreVertical, type LucideIcon } from "lucide-react";

export interface MenuAction {
  label: string;
  icon: LucideIcon;
  onSelect: () => void;
  danger?: boolean;
  disabled?: boolean;
  /** Why the action is disabled, or what it does. */
  title?: string;
}

/** The ⋮ menu of one row: closes on a choice, a click outside or Escape. */
export function ActionMenu({ label, actions }: { label: string; actions: MenuAction[] }) {
  const [open, setOpen] = useState(false);
  // Fixed to the viewport: a scrolling table would clip an absolute list.
  const [pos, setPos] = useState<{ top?: number; bottom?: number; right: number } | null>(null);
  const root = useRef<HTMLDivElement>(null);

  function toggle(button: HTMLButtonElement) {
    if (open) {
      setOpen(false);
      return;
    }
    const r = button.getBoundingClientRect();
    const right = Math.max(8, window.innerWidth - r.right);
    // Near the bottom (or above the phone's tab bar) the list opens upwards.
    const roomBelow = window.innerHeight - r.bottom;
    setPos(roomBelow < 40 * actions.length + 80 ? { bottom: window.innerHeight - r.top + 4, right } : { top: r.bottom + 4, right });
    setOpen(true);
  }

  useEffect(() => {
    if (!open) return;
    const outside = (e: MouseEvent | TouchEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    const escape = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", outside);
    document.addEventListener("touchstart", outside);
    document.addEventListener("keydown", escape);
    // The list stays where it opened; scrolling closes it instead of leaving it behind.
    const close = () => setOpen(false);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("touchstart", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  return (
    <div className="action-menu" ref={root}>
      <button
        type="button"
        className="icon-btn"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        title="More"
        onClick={(e) => toggle(e.currentTarget)}
      >
        <MoreVertical size={16} />
      </button>
      {open && (
        <div
          className="action-menu-list"
          role="menu"
          aria-label={label}
          style={pos ?? undefined}
        >
          {actions.map(({ label: text, icon: Icon, onSelect, danger, disabled, title }) => (
            <button
              key={text}
              type="button"
              role="menuitem"
              className={`action-menu-item ${danger ? "danger-item" : ""}`}
              disabled={disabled}
              title={title}
              onClick={() => {
                setOpen(false);
                onSelect();
              }}
            >
              <Icon size={14} />
              {text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
