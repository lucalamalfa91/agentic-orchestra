# Agentic Orchestra - Luxury Design System 2026

This document describes the complete design system implemented in the Agentic Orchestra frontend.

## Design Philosophy

The design system follows 6 core pillars:

1. **Glassmorphism**: Frosted glass effects with backdrop-filter blur
2. **Luxury Dark Mode**: Premium dark backgrounds with high contrast
3. **Premium Gradients**: Purple-to-violet gradients for accents
4. **Micro-interactions**: Smooth transitions and hover effects
5. **Typography**: Geist for headings, Inter for body text
6. **Animations**: Fade, slide, scale, and glow effects

## Design Tokens

All design tokens are available as CSS custom properties in `index.css`.

### Colors

```css
--color-primary: #667eea;
--color-primary-hover: #764ba2;
--color-accent: #764ba2;
--color-background: rgb(10, 10, 20);
--color-background-secondary: rgb(20, 20, 30);
--color-background-tertiary: rgb(30, 30, 45);
--color-glass: rgba(255, 255, 255, 0.1);
--color-glass-border: rgba(255, 255, 255, 0.2);
--color-text: #ffffff;
--color-text-secondary: #e0e0ff;
--color-text-tertiary: #a0a0b0;
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--gradient-primary: linear-gradient(135deg, #667eea, #764ba2);
--gradient-secondary: linear-gradient(135deg, #764ba2, #667eea);
```

### Typography

```css
--font-heading: 'Geist Variable', -apple-system, BlinkMacSystemFont, sans-serif;
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-size-xs: 0.75rem;     /* 12px */
--font-size-sm: 0.875rem;    /* 14px */
--font-size-base: 1rem;      /* 16px */
--font-size-lg: 1.125rem;    /* 18px */
--font-size-xl: 1.25rem;     /* 20px */
--font-size-2xl: 1.5rem;     /* 24px */
--font-size-3xl: 2rem;       /* 32px */
--font-size-4xl: 2.5rem;     /* 40px */
```

### Spacing

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
--spacing-3xl: 4rem;     /* 64px */
```

### Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
--shadow-glow: 0 0 20px rgba(102, 126, 234, 0.4);
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.2);
```

### Border Radius

```css
--radius-sm: 0.375rem;   /* 6px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-full: 9999px;
```

### Effects

```css
--blur-glass: 20px;
--transition-default: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

## Component Classes

### Glassmorphism Card

```jsx
<div className="glass-card">
  Content here
</div>
```

**Styles:**
- Semi-transparent background
- Backdrop blur effect
- Subtle border
- Hover lift animation

### Buttons

#### Gradient Button (Primary)
```jsx
<button className="btn-gradient">
  Click me
</button>
```

**Features:**
- Purple gradient background
- Glow shadow effect
- Lift on hover
- Minimum 44px height (WCAG AA)

#### Glass Button (Secondary)
```jsx
<button className="btn-glass">
  Click me
</button>
```

**Features:**
- Transparent background with glass effect
- Subtle border
- Hover state with increased opacity

### Inputs

```jsx
<input className="input-glass focus-ring" />
<textarea className="input-glass focus-ring" />
```

**Features:**
- Semi-transparent background
- Focus glow effect
- Accessible focus ring (WCAG 2.1 AA)
- Minimum 44px height

### Gradient Hero Section

```jsx
<div className="gradient-hero">
  <h1>Hero Title</h1>
  <p>Subtitle</p>
</div>
```

**Features:**
- Full-width purple gradient
- Centered content
- Minimum 400px height

## Animations

### Animation Classes

```jsx
<div className="animate-fade-in">Fades in</div>
<div className="animate-slide-up">Slides up</div>
<div className="animate-scale-in">Scales in</div>
<div className="animate-shimmer">Shimmer effect</div>
<div className="animate-pulse-glow">Pulsing glow</div>
```

### Animation Keyframes

- `fadeIn`: 0.6s ease-out
- `slideUp`: 0.5s ease-out (20px vertical motion)
- `scaleIn`: 0.4s ease-out (0.95 to 1.0 scale)
- `shimmer`: 2s infinite (loading state)
- `pulse-glow`: 2s infinite (glow animation)

## Accessibility

### WCAG 2.1 AA Compliance

- **Touch Targets**: Minimum 44px × 44px
- **Contrast Ratio**: 4.5:1 for text, 3:1 for UI components
- **Focus Indicators**: 2px solid outline with 2px offset
- **Keyboard Navigation**: All interactive elements accessible via keyboard

### Focus Ring

```jsx
<button className="focus-ring">Accessible button</button>
```

Auto-applied on `:focus-visible` for keyboard navigation.

### Reduced Motion Support

Users with `prefers-reduced-motion: reduce` will see instant transitions instead of animations.

### High Contrast Mode

Automatically increases border opacity and contrast for users with `prefers-contrast: high`.

## Responsive Design

### Breakpoints

- **Mobile**: 0px - 767px
- **Tablet**: 768px - 1023px
- **Desktop**: 1024px - 1279px
- **Wide**: 1280px+

### Mobile Optimizations

- Reduced font sizes (3xl: 1.75rem, 4xl: 2rem)
- Adjusted spacing
- Single column layouts
- Touch-friendly 44px minimum targets

## Usage Examples

### Card with Gradient Button

```jsx
<div className="glass-card p-8 space-y-4">
  <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text)' }}>
    Card Title
  </h2>
  <p style={{ color: 'var(--color-text-secondary)' }}>
    Card description text
  </p>
  <button className="btn-gradient w-full">
    Action Button
  </button>
</div>
```

### Gradient Text

```jsx
<h1
  style={{
    background: 'var(--gradient-primary)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text'
  }}
>
  Gradient Title
</h1>
```

### Status Badge

```jsx
<span
  style={{
    background: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    color: 'var(--color-success)',
    padding: '0.25rem 0.75rem',
    borderRadius: 'var(--radius-full)',
    fontSize: 'var(--font-size-xs)',
    fontWeight: 600
  }}
>
  Success
</span>
```

## Best Practices

1. **Always use design tokens** instead of hard-coded values
2. **Apply focus-ring** class to all interactive elements
3. **Use semantic HTML** for better accessibility
4. **Combine animations** with `animate-*` classes for polish
5. **Test with keyboard navigation** to ensure accessibility
6. **Verify contrast ratios** for all text/background combinations
7. **Use glass-card** for all container elements
8. **Apply transitions** for smooth state changes

## Color Palette Reference

| Color | Hex/RGB | Usage |
|-------|---------|-------|
| Primary | #667eea | Main brand color, buttons, links |
| Primary Hover | #764ba2 | Hover states, gradients |
| Background | rgb(10,10,20) | Main page background |
| Background Secondary | rgb(20,20,30) | Card backgrounds |
| Text | #ffffff | Primary text |
| Text Secondary | #e0e0ff | Secondary text, labels |
| Text Tertiary | #a0a0b0 | Disabled text, placeholders |
| Success | #10b981 | Success states, completed |
| Warning | #f59e0b | Warning states |
| Error | #ef4444 | Error states, failed |

## Typography Scale

| Name | Size | Line Height | Usage |
|------|------|-------------|-------|
| xs | 12px | 1.5 | Small labels, timestamps |
| sm | 14px | 1.5 | Body text, descriptions |
| base | 16px | 1.5 | Default text size |
| lg | 18px | 1.6 | Large body text, lead paragraphs |
| xl | 20px | 1.2 | Small headings, labels |
| 2xl | 24px | 1.2 | Section headings |
| 3xl | 32px | 1.2 | Page titles |
| 4xl | 40px | 1.2 | Hero titles |

## Shadow System

| Name | Use Case |
|------|----------|
| sm | Subtle elevation, inputs |
| md | Cards, dropdowns |
| lg | Modals, elevated cards |
| xl | Full-screen overlays |
| glow | Focus states, active buttons |
| inner | Inset effects, pressed states |

---

**Design System Version**: 1.0.0
**Last Updated**: 2026-04-05
**Inspired by**: Linear, Stripe, Vercel, Framer, Apple Design
