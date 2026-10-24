import { useState } from "react";
import type { LucideIcon } from "lucide-react";

export interface SubNavItem<T extends string> {
  id: T;
  label: string;
  icon: LucideIcon;
}

/**
 * Segmented sub-menu of a page (Server, Settings). The open section is kept
 * per browser, so a reload returns to it; storage may be missing or blocked.
 */
export function useSection<T extends string>(key: string, items: SubNavItem<T>[]): [T, (id: T) => void] {
  const storageKey = `ggnet.section.${key}`;
  const [section, setSection] = useState<T>(() => {
    try {
      const saved = window.localStorage.getItem(storageKey);
      const found = items.find((i) => i.id === saved);
      if (found) return found.id;
    } catch {
      // No storage: start on the first section.
    }
    return items[0].id;
  });
  const choose = (id: T) => {
    setSection(id);
    try {
      window.localStorage.setItem(storageKey, id);
    } catch {
      // Not remembered; the section still opens.
    }
  };
  // A section the user cannot see (e.g. after a role change) falls back to the first.
  return [items.some((i) => i.id === section) ? section : items[0].id, choose];
}

export function SubNav<T extends string>({
  label,
  items,
  active,
  onSelect,
}: {
  label: string;
  items: SubNavItem<T>[];
  active: T;
  onSelect: (id: T) => void;
}) {
  return (
    <div className="subnav" role="tablist" aria-label={label}>
      {items.map(({ id, label: text, icon: Icon }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={active === id}
          className={`subnav-btn ${active === id ? "active" : ""}`}
          onClick={() => onSelect(id)}
        >
          <Icon size={14} />
          {text}
        </button>
      ))}
    </div>
  );
}
