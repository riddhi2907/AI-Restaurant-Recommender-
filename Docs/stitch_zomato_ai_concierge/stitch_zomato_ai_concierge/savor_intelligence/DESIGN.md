---
name: Savor Intelligence
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1b1b1b'
  on-surface-variant: '#5b403f'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#8f6f6e'
  outline-variant: '#e4bebc'
  surface-tint: '#bb162c'
  primary: '#b7122a'
  on-primary: '#ffffff'
  primary-container: '#db313f'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3b1'
  secondary: '#006e26'
  on-secondary: '#ffffff'
  secondary-container: '#8af793'
  on-secondary-container: '#007328'
  tertiary: '#785600'
  on-tertiary: '#ffffff'
  tertiary-container: '#976d00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#8dfa96'
  secondary-fixed-dim: '#71dd7c'
  on-secondary-fixed: '#002106'
  on-secondary-fixed-variant: '#00531b'
  tertiary-fixed: '#ffdea6'
  tertiary-fixed-dim: '#ffbb0c'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5d4200'
  background: '#fcf9f8'
  on-background: '#1b1b1b'
  surface-variant: '#e5e2e1'
typography:
  page-title:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  section-title:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  card-title:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: '1.5'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.2'
    letterSpacing: 0.01em
  page-title-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.2'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style

The design system is engineered for a high-utility, consumer-centric AI restaurant recommendation platform. The brand personality is **appetizing, reliable, and effortless**, blending the energetic heritage of food discovery with the precision of modern AI. 

The aesthetic follows a **Modern Corporate** style with subtle **Minimalist** influences. It prioritizes clarity and high-quality imagery above all else. The interface is intentionally "invisible" to allow food photography and restaurant data to remain the focal point. By utilizing generous white space and a structured hierarchy, the design system ensures a trustworthy experience for users making quick dining decisions in a high-density urban context.

## Colors

This design system utilizes a high-contrast palette optimized for legibility and appetite appeal. 

- **Primary Red**: Reserved for critical actions, branding, and primary CTAs. It signifies urgency and passion for food.
- **Success Green**: Specifically allocated for ratings, "Open Now" indicators, and health-positive attributes.
- **Neutral Palette**: A range of off-whites and greys are used to create structural depth without competing with vibrant food photography.
- **Interactive States**: Use a 10% black overlay for hover states on primary buttons and a 5% black overlay for pressed states.

## Typography

The system uses **Inter** exclusively to maintain a systematic, utilitarian, and modern feel. 

- **Hierarchy**: Use `page-title` for main view headings and `section-title` for grouping content like "Trending in Indiranagar" or "AI Recommendations."
- **Readability**: Body text should primarily use the 14px `body-md` for descriptions and meta-data to maximize information density.
- **Emphasis**: Semibold weights are used strictly for navigation and titles to ensure a clear scannability path for the user.

## Layout & Spacing

The design system employs a **Fluid Grid** model based on a 4px baseline shift. 

- **Mobile (Default)**: A 4-column grid with 16px margins and 16px gutters.
- **Desktop**: A 12-column centered grid with a max-width of 1200px.
- **Spacial Logic**: Use `md` (16px) for internal card padding and `lg` (24px) for vertical spacing between logical sections. Elements related to each other (like a label and an input) should use `xs` (8px).

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and subtle **Ambient Shadows**.

- **Level 0 (Background)**: `#F8F8F8` – The base canvas.
- **Level 1 (Surface)**: `#FFFFFF` – Used for cards, sheets, and inputs. 
- **Shadows**: Cards utilize a soft, diffused shadow: `0 2px 8px rgba(0,0,0,0.08)`. This creates a "lifted" effect that distinguishes interactive content from the static background.
- **Interactive Depth**: On tap/click, cards should transition to a `0 1px 4px rgba(0,0,0,0.04)` shadow to simulate a physical press.

## Shapes

The shape language is friendly yet structured. 

- **Cards & Containers**: Use a **12px** radius (`rounded-lg`) to evoke a modern, consumer-app feel.
- **Inputs & Buttons**: Use an **8px** radius to maintain a sense of precision and functional clarity.
- **Badges/Tags**: Use a **Full Radius (Pill)** for status tags and category chips to differentiate them from actionable buttons.

## Components

### Buttons
- **Primary**: Full-width, #E23744 background, white text, 8px radius. High emphasis.
- **Secondary**: White background, #E23744 border (1px), #E23744 text.
- **Ghost**: No background/border, #696969 text, used for secondary actions like "View All."

### Form Fields & Inputs
- **Text Inputs**: 8px radius, #E8E8E8 border. On focus, the border transitions to #E23744 with a 2px outer glow.
- **Segmented Controls**: Used for Budget (₹, ₹₹, ₹₹₹). The container is #F8F8F8; the selected segment is #E23744 with white text and a subtle shadow.
- **Sliders**: The track is #E8E8E8, the active fill is #E23744, and the thumb is a 24px white circle with a 1px border.

### Cards
- **Restaurant Card**: 12px radius, white surface, shadow-sm. Features a top-aligned image (16:9 ratio), title in `card-title`, and a secondary row for cuisine/location.
- **Rating Badge**: A small pill with #24963F background and white text, usually anchored to the top-right of the image or next to the title.

### AI Indicators
- Use a subtle gradient or a "Sparkle" icon in Primary Red to denote recommendations generated specifically by the AI engine.