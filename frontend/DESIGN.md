<!-- SEED: re-run /impeccable document once there's code to capture the actual tokens and components. -->
---
name: Hermes
description: A calm academic chat agent for USP students making clearer course and curriculum decisions.
---

# Design System: Hermes

## 1. Overview

**Creative North Star: "Quiet Academic Guide"**

Hermes is a light-first product interface for students who are trying to reduce academic uncertainty, not admire interface decoration. The system should feel modern, clear, technological, elegant, and minimalist, with the conversation treated as the primary product surface.

The design language is restrained and deliberate: warm light surfaces, careful typography, visible interaction states, and one golden accent used with discipline. The interface should feel like a capable academic guide, not a generic assistant trying to impress the user.

Hermes explicitly rejects chaotic, polluted, noisy, or overdecorated UI. It must avoid generic AI dashboard patterns, excessive gradients, busy decorative effects, novelty chatbot styling, and interfaces that feel like AI-generated SaaS templates.

**Key Characteristics:**
- Calm, readable, and task-focused.
- Light-first, with enough warmth to feel approachable.
- Conversation-centered, with no unnecessary dashboard framing.
- Restrained golden emphasis, never decorative saturation.
- Predictable controls with clear keyboard and loading states.

## 2. Colors

Hermes uses a restrained palette: tinted neutrals carry the interface, and gold appears only when it clarifies priority, brand identity, or action.

### Primary
- **Hermes Gold** (#dbb05b): The sole brand accent. Use for the primary send action, focused highlights, selected states, and rare brand moments. It should occupy less than 10% of any normal product screen.

### Neutral
- **Warm Academic Surface** ([to be resolved during implementation]): The page background and broad reading surface. It should be light, warm, and never pure white.
- **Soft Panel Surface** ([to be resolved during implementation]): The input bar, message containers, and subtle UI panels. It should separate layers without turning the chat into a card grid.
- **Primary Ink** ([to be resolved during implementation]): Main text. It should be dark enough for WCAG AA contrast, but never pure black.
- **Quiet Border** ([to be resolved during implementation]): Dividers, input outlines, and subtle separation. It should support structure without visual noise.

### Named Rules

**The One Gold Rule.** Hermes Gold is the only accent. Do not introduce secondary accent colors until the product has a real semantic need.

**The Less Than Ten Rule.** Gold must remain rare in normal chat UI. Its scarcity is what makes it useful.

## 3. Typography

**Display Font:** [font to be chosen during implementation]
**Body Font:** single sans direction, warm and precise
**Label/Mono Font:** [only add if a real product need appears]

**Character:** Typography should feel native, academic, and quietly technical. Product readability matters more than brand flourish.

### Hierarchy
- **Display** ([to be resolved during implementation]): Reserved for the first empty-state invitation or one-time onboarding moment. Do not use display typography inside routine chat controls.
- **Headline** ([to be resolved during implementation]): Used for compact page or state headings when needed.
- **Title** ([to be resolved during implementation]): Used for message group labels, dialogs, or settings surfaces if those appear later.
- **Body** ([to be resolved during implementation]): The core chat reading style. Long-form assistant responses should stay comfortable at 65-75ch when space allows.
- **Label** ([to be resolved during implementation]): Used for buttons, helper text, and form labels. Labels should be clear, not stylized.

### Named Rules

**The Reading First Rule.** If a typographic choice makes a student read slower, it is wrong for Hermes.

## 4. Elevation

Hermes should be flat by default. Depth comes from tonal layering, borders, and spacing before shadows. Shadows may appear on transient elements or focused controls only when they clarify state.

### Named Rules

**The Flat Chat Rule.** The chat surface is not a stack of decorative cards. Use elevation only for active, floating, or temporary elements.

## 5. Components

No component library exists yet. The first implementation should define only the primitives needed for the MVP chat: message bubbles or message rows, text input, send button, loading state, empty state, and accessible focus states.

### Buttons
- **Shape:** gently curved, compact, and product-native ([radius to be resolved during implementation]).
- **Primary:** Hermes Gold for the send action only, with sufficient contrast and a clear disabled state.
- **Hover / Focus:** visible and purposeful. Focus must be keyboard-obvious and must not rely on color alone.

### Inputs / Fields
- **Style:** calm, spacious, and readable. The input should feel like the center of action, not a search bar pasted into a dashboard.
- **Focus:** clear outline or tonal shift with a gold reference used sparingly.
- **Disabled / Loading:** explicit and understandable, with no silent failure states.

### Message Surface
- **Style:** conversation-first. Prefer readable message rows and subtle role distinction over decorative chat bubbles.
- **Assistant Responses:** optimized for scanning academic explanations, lists, and curriculum comparisons.
- **User Messages:** clear ownership without saturated color blocks.

## 6. Do's and Don'ts

### Do:
- **Do** make the conversation central.
- **Do** use Hermes Gold (#dbb05b) as the single accent for primary action, focus, and selected state.
- **Do** keep every surface calm, readable, and intentional.
- **Do** use motion to clarify state changes, never to decorate.
- **Do** build visible focus states, readable text sizing, clear send, disabled, and loading states.
- **Do** treat Portuguese as the primary language context when writing UI copy.

### Don't:
- **Don't** make Hermes look chaotic, polluted, noisy, or overdecorated.
- **Don't** use generic AI dashboard patterns.
- **Don't** use excessive gradients.
- **Don't** use busy decorative effects.
- **Don't** use novelty chatbot styling.
- **Don't** create an interface that feels like an AI-generated SaaS template.
- **Don't** bury the chat experience under unnecessary navigation, cards, metrics, history panels, or feature marketing.
- **Don't** add a second accent color unless a real semantic state requires it.
- **Don't** rely on color alone to communicate meaning.
