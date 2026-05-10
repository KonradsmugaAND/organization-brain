# WenetBrain Design System

This document defines the visual language and UI patterns for the WenetBrain frontend.

> **Tech Stack**: React 19 + TypeScript + Vite + shadcn/ui (Radix UI + Tailwind CSS v4) + lucide-react icons.
> Both the main app (`app/frontend/`) and admin panel (`admin/frontend/`) share this design system.

---

## 1. CSS Architecture (Tailwind v4)

We use the **Tailwind v4 four-step architecture**:

1. **Define CSS variables at `:root` level** (NOT inside `@layer base`) using `hsl()` wrapper
2. **Map variables to utilities** via `@theme inline`
3. **Apply base styles** in `@layer base` using unwrapped `var(--name)`
4. **Dark mode** switches automatically via `.dark` class on `<html>`

### Critical Rules
- Colors in `:root` and `.dark` MUST use `hsl()` wrapper
- `@theme inline` generates utility classes (`bg-background`, `text-primary`)
- Never use `tailwind.config.ts` in v4 (delete if exists)
- Never double-wrap: `var(--background)` NOT `hsl(var(--background))`
- Never use `dark:` variants for semantic colors

---

## 2. Color Palette

### Core Neutral Colors
| Token | Light | Dark | Usage |
| :--- | :--- | :--- | :--- |
| `--color-background-primary` | `hsl(0 0% 100%)` | `hsl(222.2 84% 4.9%)` | Main content area background |
| `--color-background-secondary` | `hsl(210 40% 96.1%)` | `hsl(217.2 32.6% 17.5%)` | Sidebar, Topbar, and Card backgrounds |
| `--color-background-tertiary` | `hsl(210 40% 96.1%)` | `hsl(217.2 32.6% 17.5%)` | Subtle backgrounds, disabled fields |
| `--color-text-primary` | `hsl(222.2 84% 4.9%)` | `hsl(210 40% 98%)` | Headings, active text, primary labels |
| `--color-text-secondary` | `hsl(215.4 16.3% 46.9%)` | `hsl(215 20.2% 65.1%)` | Body text, inactive items |
| `--color-text-tertiary` | `hsl(240 5.3% 26.1%)` | `hsl(240 4.8% 95.9%)` | Metadata, placeholders, disabled state *(min 4.5:1 contrast)* |
| `--color-border-primary` | `hsl(214.3 31.8% 91.4%)` | `hsl(217.2 32.6% 17.5%)` | Main structural dividers |
| `--color-border-secondary` | `hsl(214.3 31.8% 91.4%)` | `hsl(217.2 32.6% 17.5%)` | Input borders, button borders |
| `--color-border-tertiary` | `hsl(220 13% 91%)` | `hsl(240 3.7% 15.9%)` | Subtle section separators |

### Brand / CTA Colors
| Token | Light | Dark | Usage |
| :--- | :--- | :--- | :--- |
| `--color-primary` | `hsl(222.2 47.4% 11.2%)` | `hsl(210 40% 98%)` | Primary buttons, CTA backgrounds |
| `--color-primary-hover` | `hsl(210 40% 98%)` | `hsl(222.2 47.4% 11.2%)` | Primary button hover |
| `--color-primary-foreground` | `hsl(210 40% 98%)` | `hsl(222.2 47.4% 11.2%)` | Text on primary buttons |
| `--color-accent` | `hsl(210 40% 96.1%)` | `hsl(217.2 32.6% 17.5%)` | Links, info badges, focus rings |
| `--color-accent-hover` | `hsl(222.2 47.4% 11.2%)` | `hsl(210 40% 98%)` | Accent hover state |

### Semantic Colors
| Token | Value | Usage |
| :--- | :--- | :--- |
| `--color-success` | `hsl(142.1 76.2% 36.3%)` | Success states, approve actions |
| `--color-warning` | `hsl(38 92% 50%)` | Warnings |
| `--color-danger` | `hsl(0 84.2% 60.2%)` | Errors, destructive actions |
| `--color-info` | `hsl(221.2 83.2% 53.3%)` | Informational highlights |

### Space-Specific "Bank" Colors
Used for identifying the source/context of a note or decision.
| Space Type | Background Token | Text Token |
| :--- | :--- | :--- |
| **WeAll** (root) | `--color-bank-weall-bg` | `--color-bank-weall-text` |
| **Company** | `--color-bank-comp-bg` | `--color-bank-comp-text` |
| **Team** | `--color-bank-team-bg` | `--color-bank-team-text` |
| **Group** | `--color-bank-group-bg` | `--color-bank-group-text` |
| **Private** | `--color-bank-priv-bg` | `--color-bank-priv-text` |

Bank colors are defined in `@theme inline` and map to HSL values consistent with the design system.

---

## 3. Typography & Spacing

- **Font Stack**: `'Geist Variable', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Border Radius Tokens**:
    - Small (`--radius-sm`): `calc(var(--radius) * 0.6)`
    - Medium (`--radius-md`): `calc(var(--radius) * 0.8)` — Buttons, Inputs
    - Large (`--radius-lg`): `var(--radius)` — Cards, Main Shell
    - XL (`--radius-xl`): `calc(var(--radius) * 1.4)`
- **Spacing Scale**:
    - Base unit: `4px`
    - Padding: `12px` (Standard), `16px` (Content areas)

---

## 4. Component Patterns

### Bank Pill
A compact badge indicating the organizational context.
- **Style**: `display: inline-flex; align-items: center; font-size: 11px; padding: 2px 8px; border-radius: 10px;`
- **Colors**: Use `--color-bank-{type}-bg` and `--color-bank-{type}-text` tokens

### Refined Inbox Card
Used for items requiring approval or review.
- **Structure**:
    - **Header**: [Bank Pill] + [Author Metadata]
    - **Title**: Bold, primary text, 13px
    - **Body**: Secondary text, 12px, line-height 1.5
    - **Meta**: Tertiary text, 11px (Date, Source)
    - **Actions**: Row of semantic buttons (Approve: `--color-success`, Reject: `--color-danger`, Export: `--color-accent`)

### Persistent Chat Area
A vertical column on the right of the workspace.
- **Header**: Space Name (e.g., "Asystent WenetBrain")
- **Messages**: User (`--color-accent` background), AI (`--color-background-secondary` background)
- **Input**: Bottom-aligned, minimal border, "Up" arrow send button.

---

## 5. Layout Architecture

`Shell` → `Topbar` (Top) + `Sidebar` (Left) + `Main Workspace` (Center/Right)
`Main Workspace` → `Content Area` (Left, 1fr) + `Chat Area` (Right, 360px)
`Content Area` → Tabbed views (Inbox, Notes, Settings, Search)

---

## 6. Accessibility Rules

- Minimum contrast ratio **4.5:1** for all normal text.
- Focus rings must be visible (`box-shadow: 0 0 0 3px rgba(37,99,235,0.15)` on accent, or `outline: 2px solid` on primary).
- **No emoji as UI icons** — always use Google Material Icons (`<span class="material-icons-outlined">name</span>`) or `lucide-react` for interactive elements.
- Touch targets minimum **44×44 px**.

---

## 7. File Structure

```
app/frontend/src/
  index.css          # Tailwind v4 setup + theme tokens
  main.tsx           # React 19 root (StrictMode)
  App.tsx            # Root component
  api.ts             # HTTP client + types
  lib/
    utils.ts         # cn() utility
  components/
    Layout.tsx       # Shell (Topbar + Sidebar + Chat)
    NotesView.tsx    # Notes list
    InboxView.tsx    # Inbox / HITL queue
    SearchView.tsx   # Search results
    SettingsView.tsx # User settings
    MeetingModal.tsx # Meeting upload/record
    NoteModal.tsx    # Create note dialog
    ui/              # shadcn/ui components
```
