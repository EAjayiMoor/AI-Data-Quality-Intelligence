# UI Compliance Checklist (Moorhouse Standard)

Source standard: `C:\Users\EmmanuelAjayi\Documents\Moorhouse-UI-Standard.md`

Purpose: provide a phase-mapped implementation checklist so this PoC aligns with the Moorhouse UI contract from first working UI increment.

## 1) Non-negotiable baseline

- Use design tokens only; do not hard-code visual hex values.
- Prioritise data clarity over decoration; avoid gradients, glass effects, and decorative shadows.
- Keep one clear primary action per view.
- Use sentence case and British English in UI copy.
- No emoji and no exclamation marks in product UI.
- Ensure keyboard parity and visible focus state for every interactive control.
- Never use colour as the only signal for status or errors.

## 2) Tokens and styling controls

- Use Moorhouse token roles for brand, accent, warning, and error states.
- Use semantic text and background tokens for body and surface styling.
- Keep spacing on a consistent scale; avoid arbitrary one-off spacing values.
- Keep radius and shadow usage consistent with shared component style.
- Honour `prefers-reduced-motion` and avoid animated layout changes.

## 3) Accessibility gates (WCAG 2.1 AA floor)

- Verify text and UI contrast meets AA thresholds.
- Ensure all interactive elements are Tab reachable.
- Keep `:focus-visible` styling enabled globally.
- Use semantic controls first (`button`, `input`, `nav`, `main`).
- Add `aria-label` to icon-only controls.
- Associate field errors with controls using `aria-describedby`.
- Ensure 200% zoom reflow without horizontal scroll below desktop breakpoints.

## 4) Status and data communication

- Statuses and exceptions must display with label + icon + colour.
- Use calm default palette; reserve loud colours for exceptions and risks.
- Keep tables legible with tabular number alignment where appropriate.
- Keep empty states explicit and factual; avoid mock data visual placeholders.

## 5) Component usage rules

- Prefer shared, reusable UI patterns over one-off custom visual controls.
- Wrap form inputs with consistent field structure (label, hint, validation).
- Use destructive styles only for truly destructive actions.
- Add new component variants only when required and documented.

## 6) Phase mapping for this PoC

### Phase 4 (current: retrieval layer)
- No major UI work expected.
- Prepare response shapes that support explicit status labels and exception metadata.

### Phase 5 (assessment contract and validation)
- Ensure response contract includes display-ready status labels and confidence categories.
- Ensure exception categories are user-readable and icon-mappable.

### Phase 6 (LLM adapter and cost capture)
- Provide deterministic, display-ready cost and usage fields.
- Ensure failure states are structured for accessible inline messaging.

### Phase 7 (UI flow and interaction)
- Apply full checklist before sign-off.
- Run keyboard-only walkthrough for primary user path.
- Run 200% zoom pass and reduced-motion pass.

### Phase 8 (verification and release)
- Include UI compliance pass in release checklist.
- Record any temporary UI deviations as explicit known limitations.

## 7) UI sign-off template

Use this at phase-end UI checkpoints:

- Tokens only: pass/fail
- Typography and copy rules: pass/fail
- Status signal redundancy (label+icon+colour): pass/fail
- Keyboard parity and visible focus: pass/fail
- Contrast and zoom checks: pass/fail
- Reduced motion behaviour: pass/fail
- Component consistency: pass/fail
- Open deviations and remediation owner/date


## 8) Current implementation status (Phase 10)

- Tokens and brand colour mapping: **implemented in Streamlit CSS layer**.
- Sentence-case copy and plain language: **implemented across executive, assessment, and exceptions pages**.
- Emoji/exclamation policy: **pass**.
- Status signalling with label + colour + text: **implemented via risk callouts and status pills**.
- Focus visibility: **implemented via global `:focus-visible` styling**.
- Reduced motion handling: **implemented via `prefers-reduced-motion` rule**.
- Remaining gap: full component parity with React/Tailwind reference remains partial due Streamlit native-widget constraints.
