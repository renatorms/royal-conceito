import { ChevronDownIcon } from "lucide-react";

// Reusable open/close shell for a Header nav item that reveals a panel —
// "Roupas" and "Marcas" today (see HeaderNav.jsx). Purely presentational:
// the caller owns the data and the panel's own layout via `children`, this
// only handles hover/focus/tap mechanics. Extracted from the old
// MegaMenu.jsx (a single catch-all "Categorias" trigger) when the Header
// was redesigned around several distinct top-level nav items instead — see
// CLAUDE.md for the full redesign.
export function NavDropdown({ label, children }) {
  return (
    <>
      {/* Desktop: pure-CSS hover/focus reveal, no React state — same
          mechanism the old MegaMenu.jsx used. `hidden` (not opacity/
          visibility) while closed keeps the panel's links out of the tab
          order until group-hover/group-focus-within shows it; tabbing onto
          the trigger button itself also opens it (:focus-within matches
          the trigger too, since it's inside the same `group`). Panel is
          centered under the trigger (`left-1/2 -translate-x-1/2`), not
          left-aligned like the old single-trigger menu — this trigger can
          now sit anywhere in a centered nav row, so anchoring from its own
          center reads better than always hanging off its left edge. */}
      <div className="group relative hidden md:block">
        <button
          type="button"
          aria-haspopup="true"
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
        >
          {label}
          <ChevronDownIcon className="size-3.5 transition-transform group-hover:rotate-180 group-focus-within:rotate-180" />
        </button>

        <div className="absolute left-1/2 top-full z-50 hidden w-max min-w-[220px] max-w-3xl -translate-x-1/2 rounded-b-md border border-t-0 border-border bg-popover p-6 text-popover-foreground shadow-lg group-hover:block group-focus-within:block">
          {children}
        </div>
      </div>

      {/* Mobile: hover doesn't exist on touch — native <details>/<summary>
          gives a tap-to-expand disclosure with no React state, same
          pattern used here before the redesign. Renders inline in the nav
          flow (not absolutely positioned), so opening it pushes the rest
          of the row down, standard accordion behavior. */}
      <details className="group md:hidden">
        <summary className="flex cursor-pointer list-none items-center gap-1 text-muted-foreground hover:text-foreground [&::-webkit-details-marker]:hidden">
          {label}
          <ChevronDownIcon className="size-3.5 transition-transform group-open:rotate-180" />
        </summary>
        <div className="mt-3 border-t border-border pt-3">{children}</div>
      </details>
    </>
  );
}
