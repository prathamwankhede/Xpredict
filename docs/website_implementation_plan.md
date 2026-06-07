# Prediction Market Website Implementation Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. This plan must be maintained in accordance with [.agents/PLANS.md](.agents/PLANS.md).

## Purpose / Big Picture

Deliver a visually premium, interactive prediction market website that communicates trust, speed, and liquidity at a glance, while providing a usable market detail and trading experience. A user should be able to open the site in a browser, browse markets, see a highlighted market with YES/NO pricing, open a market detail view, and interact with a trading terminal UI that reflects the platform mechanics. This plan emphasizes UI polish per the design guidance in [docs/implementation_plan.md](docs/implementation_plan.md), section 6, with a clear, testable visual result.

## Progress

- [x] (2026-06-01 22:15Z) Confirmed frontend scaffold approach and recorded baseline environment (node v18.16.1, npm 9.5.1, yarn 1.22.22; pnpm not installed).
- [x] (2026-06-01 23:07Z) Stand up the frontend project structure and establish global design tokens, typography, and background atmosphere (completed: Svelte + Vite app in ./frontend, global tokens + glassmorphism + fonts wired, Tailwind v4 PostCSS plugin configured).
- [x] (2026-06-01 23:07Z) Implement the home and markets views with the hero, filters, bento cards, and activity ticker.
- [x] (2026-06-01 23:07Z) Implement the market detail view with chart area, orderbook, and trading terminal panels.
- [x] (2026-06-01 23:08Z) Add search overlay, micro-animations, accessibility polish, and responsive behavior (completed: search overlay, animations, responsive layout, focus-visible styling, reduced-motion fallback).
- [x] (2026-06-01 23:08Z) Validate the UI locally and document expected outcomes (ran `npm run dev -- --host` from ./frontend; Vite ready on http://localhost:5173).

## Surprises & Discoveries

- Observation: `npm create vite@latest` failed on Node v18.16.1 because create-vite@9 requires Node >=20.19 and uses `node:util` exports that are not present in Node 18.
  Evidence: `npm WARN EBADENGINE required: { node: '^20.19.0 || >=22.12.0' }` and `SyntaxError: The requested module 'node:util' does not provide an export named 'styleText'`.

- Observation: Tailwind v4 no longer supports `tailwindcss init`, so PostCSS is configured manually and styles use `@import "tailwindcss"`.
  Evidence: Tailwind v4 install uses `@tailwindcss/postcss` plugin with a `postcss.config.js` file; no init step is required.

## Decision Log

- Decision: Use the visual language described in section 6 of [docs/implementation_plan.md](docs/implementation_plan.md) (dark base, glassmorphism, fintech polish), while selecting non-default typography that still conveys the same tone.
  Rationale: The UI guidance mandates a premium dark theme and glass effects, but the execution must avoid default font stacks; using Sora for UI text and Space Grotesk for display maintains the intended vibe without relying on the default Inter pairing.
  Date/Author: 2026-05-31 / Copilot

- Decision: Focus the first implementation on a fully working, front-end-only experience with deterministic mock data, with an explicit path to wire into the existing API later.
  Rationale: The repository’s API endpoints in [api.py](api.py) do not currently expose a market listing endpoint, and a website demonstration must remain functional without backend changes.
  Date/Author: 2026-05-31 / Copilot

- Decision: Keep the existing [index.svelte](index.svelte) file as a design reference and seed content source for the root UI layout.
  Rationale: The current repository already includes a Svelte entry, and reusing it reduces risk and keeps the plan anchored to existing assets.
  Date/Author: 2026-05-31 / Copilot

- Decision: Scaffold the frontend in a dedicated ./frontend folder instead of the repository root.
  Rationale: The repository root contains backend files; the Vite scaffold requires an empty directory unless explicitly overwriting, and the user selected a subfolder to avoid conflicts.
  Date/Author: 2026-06-01 / Copilot

- Decision: Use Tailwind v4 with the `@tailwindcss/postcss` plugin and `@import "tailwindcss"` in the global stylesheet, without a Tailwind config file unless custom tokens are needed.
  Rationale: Tailwind v4 removed the init workflow; PostCSS configuration keeps the setup minimal and consistent with the v4 toolchain.
  Date/Author: 2026-06-01 / Copilot

## Outcomes & Retrospective

This plan is newly drafted; no outcomes yet. Update this section after the first milestone is completed.

## Context and Orientation

The repository currently contains a FastAPI backend in [api.py](api.py) and a minimal Svelte entry point in [index.svelte](index.svelte). The frontend scaffold now lives in ./frontend. The plan focuses on building a user-facing website experience first, with mock data, then optionally wiring in the API. The UI must align to section 6 of [docs/implementation_plan.md](docs/implementation_plan.md), which specifies a premium dark theme, glassmorphism, and a component hierarchy centered on a hero spotlight, market filter grid, and bento-style market cards. “CLOB” means Central Limit Order Book, the live list of bids and asks. “TWPM” means Time-Weighted Pari-Mutuel, a pooled market with time-weighted bets. “Glassmorphism” means semi-transparent surfaces with blur and soft borders that make UI layers look like frosted glass.

## Milestones

Milestone 1 establishes the frontend project scaffolding and global styling foundation, ending with a running dev server that shows a styled shell with the correct background, typography, and layout grid. The acceptance for this milestone is visual: the header, background, and card surfaces match the palette and glass specification.

Milestone 2 builds the home and markets experience, ending with a hero market spotlight, filter pills, a bento grid of market cards, and a live activity ticker, all using mock data. The acceptance is that users can scroll through cards, see YES/NO pricing buttons, and observe a responsive layout on mobile width.

Milestone 3 builds the market detail view and trading terminal, ending with a split layout that includes a chart area, orderbook table, and a trade form that switches between BUY/SELL and shows TWPM-specific fields when toggled. The acceptance is that UI interactions update state immediately and remain accessible, with all components aligned to the visual system.

## Plan of Work

Start by creating a frontend project structure in the ./frontend folder using the standard Svelte + Vite scaffolder and replace the generated root component’s markup with the content from [index.svelte](index.svelte), then expand it into a full layout. Establish design tokens in the global stylesheet using the palette from section 6 of [docs/implementation_plan.md](docs/implementation_plan.md), but apply Sora for body/UI and Space Grotesk for display to respect the “no default stacks” rule. Implement a layered background with a subtle gradient and soft radial glow, plus faint noise to keep the scene atmospheric and non-flat. Implement glassmorphism as a reusable class with a translucent background, blur, and border.

Next, build the home and markets views with the component hierarchy described in section 6: a hero spotlight, a market filter grid, and a bento card list. Use mock data to render multiple markets with engine badges, sparklines, and YES/NO quick-bet buttons. Add a live activity ticker that animates across the top or bottom of the screen and uses color-coded text for buy/sell actions. Ensure all components are responsive with a mobile-first layout.

Finally, build the market detail view with a left column for title, countdown, and a chart container, and a right column for the trading terminal. The terminal should include segmented BUY/SELL toggles, tabs for Market/Limit/Pari-Mutuel, and input fields for size and price, with a computed summary that shows estimated slippage or time-weight premium when TWPM is selected. Add a search overlay opened by Cmd/Ctrl+K, micro-animations for card entrance and orderbook flashes, and accessibility checks for contrast and focus states.

## Starting the Vite Dev Server

To run and view the prediction market website locally:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies (if you haven't already):
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Access the application in your browser at the printed local address (default is **http://localhost:5173**).

## Concrete Steps

From the repository root, create the frontend scaffold in ./frontend and install dependencies using the standard Svelte + Vite tooling. Then, replace the generated root component content with the markup from [index.svelte](index.svelte) and expand it into the full layout described above. Start the dev server from ./frontend and verify the UI in a browser.

Example command sequence (run from the repository root):

  npm create vite@latest frontend -- --template svelte
  cd frontend
  npm install
  npm run dev

When the dev server is running, open the local URL it prints (usually http://localhost:5173) and confirm the layout renders.

## Validation and Acceptance

Acceptance is visual and interaction-based. The homepage must show a hero spotlight, filter pills, and a bento grid with at least six mock markets. The market cards must display engine badges (CLOB or TWPM), a sparkline or placeholder chart, and two quick-bet buttons with YES/NO percentages. The market detail view must show a split layout with a chart area, an orderbook grid, and a trading terminal that toggles between BUY/SELL and order types. The search overlay must open with Cmd/Ctrl+K, trap focus, and close on Escape. The site must be usable at mobile width and maintain WCAG AA contrast for primary text.

## Idempotence and Recovery

All steps are additive. If the frontend scaffolding has already been created, skip the scaffolding command and proceed to styling and UI work. If the scaffold command adds files that conflict with existing root files, create a backup copy of the repository and rerun the scaffold, or rerun the scaffold in a fresh directory and then move the generated files into the repository root. Re-running `npm install` and `npm run dev` is safe.

## Artifacts and Notes

Expected dev server output should resemble:

    VITE vX.Y.Z  ready in N ms
    ➜  Local:   http://localhost:5173/
    ➜  Network: use --host to expose

A successful visual check shows a dark, glassmorphic interface with teal/cyan accents, green (YES) and rose (NO) call-to-action buttons, and smooth entrance animations on cards.

## Interfaces and Dependencies

Use Svelte with Vite for the frontend runtime and hot-reload, Tailwind CSS for utility styling plus a small set of custom CSS variables for tokens, and a lightweight chart library for sparklines if needed. Use a motion library (or Svelte’s built-in transitions) for entrance and status animations. Use a small state store for UI toggles and the search overlay, and plan a future integration layer that can call the endpoints in [api.py](api.py) without blocking the UI on backend availability. All dependencies should be pinned in the project’s package manager lockfile.

Change note: Initial plan created on 2026-05-31 to outline the website implementation per section 6 of [docs/implementation_plan.md](docs/implementation_plan.md) and to comply with [.agents/PLANS.md](.agents/PLANS.md).
Change note: 2026-06-01 recorded the Node version blocker from the scaffold attempt and updated Progress/Surprises accordingly.
Change note: 2026-06-01 moved the frontend scaffold location to ./frontend to avoid overwriting root files, and updated the plan to match.
Change note: 2026-06-01 marked Milestone 1-3 UI implementation progress and documented the Tailwind v4 setup.
Change note: 2026-06-01 completed accessibility polish and validation steps after verifying the dev server output.