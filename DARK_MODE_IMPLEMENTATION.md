# Dark Mode Implementation Guide

## Overview
VishwaGuru now supports a complete dark mode implementation with system preference detection, localStorage persistence, and smooth transitions between themes.

## Features Implemented

### 1. **Theme Context Provider** (`src/contexts/ThemeContext.jsx`)
- Centralized theme state management
- System preference detection using `prefers-color-scheme` media query
- localStorage persistence for user preference
- Custom `useTheme()` hook for easy integration

### 2. **Dark Mode Toggle Button** (`src/components/DarkModeToggle.jsx`)
- Located in the header for easy access
- Smooth icon transitions using Lucide React icons (Sun/Moon)
- Accessible with proper ARIA labels and tooltips
- Responsive button styling with hover effects

### 3. **Tailwind CSS Dark Mode Support**
- Updated `tailwind.config.js` to use `darkMode: 'class'` strategy
- All components use Tailwind's `dark:` prefix for dark mode styles
- Smooth transitions between themes (300ms)

### 4. **Global Styling Updates**
- **`src/index.css`**: Added dark mode base styles and layer utilities
- **`src/App.css`**: Added dark mode color variables and background gradients
- **`src/App.jsx`**: Updated all components with dark mode classes
- Consistent styling across light and dark themes

## How It Works

### Theme Detection Order
1. **User Preference (localStorage)**: If user has previously selected a theme, that preference is used
2. **System Preference (prefers-color-scheme)**: If no user preference is saved, the system preference is detected
3. **Default**: Light mode is the default fallback

### Theme Persistence
- User's theme choice is saved to localStorage with key `theme-preference`
- Preference persists across page reloads and browser sessions
- Automatically responds to system theme changes if no user preference is set

### Component Styling
Dark mode styles are applied using Tailwind's `dark:` prefix:

```jsx
<div className="bg-white dark:bg-[#2d2d2d] text-gray-900 dark:text-gray-100">
  Content
</div>
```

## Files Modified/Created

### Created Files
- `src/contexts/ThemeContext.jsx` - Theme context provider
- `src/components/DarkModeToggle.jsx` - Dark mode toggle button

### Modified Files
- `src/main.jsx` - Wrapped App with ThemeProvider
- `src/App.jsx` - Integrated DarkModeToggle and dark mode classes
- `src/index.css` - Added dark mode global styles
- `src/App.css` - Added dark mode CSS variables and backgrounds
- `tailwind.config.js` - Enabled dark mode with class strategy

## Usage in Components

### Using the Theme Hook
```jsx
import { useTheme } from './contexts/ThemeContext';

function MyComponent() {
  const { isDark, toggleTheme, mounted } = useTheme();
  
  if (!mounted) return null; // Prevent hydration mismatch
  
  return (
    <button onClick={toggleTheme}>
      {isDark ? 'Light Mode' : 'Dark Mode'}
    </button>
  );
}
```

### Styling with Dark Mode
```jsx
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  This adapts to dark mode automatically
</div>
```

## Color Scheme

### Light Mode
- Background: White/Light Gray
- Text: Dark Gray (#1f2937)
- Borders: Light Gray (#e5e7eb)
- Cards: White with transparency

### Dark Mode
- Background: #1a1a1a (primary), #2d2d2d (secondary)
- Text: Light Gray (#f3f4f6)
- Borders: Dark Gray (#404040)
- Cards: #2d2d2d with transparency

## Browser Support
- Modern browsers with CSS custom properties support
- System preference detection via CSS media queries
- localStorage API for persistence
- Smooth transitions via CSS transitions

## Performance Considerations
- No additional dependencies required (uses native CSS and React context)
- Minimal re-renders due to efficient context management
- `mounted` state prevents hydration mismatches in SSR scenarios

## Testing Dark Mode

### Manual Testing
1. Click the theme toggle button in the header
2. Verify the theme switches smoothly
3. Reload the page - theme preference should persist
4. Change system theme in OS settings - verify auto-switch (if no user preference set)

### Browser DevTools Testing
1. Open DevTools (F12)
2. Open Command Palette (Cmd+Shift+P or Ctrl+Shift+P)
3. Search for "Emulate CSS media feature prefers-color-scheme"
4. Test with both "prefers-color-scheme: dark" and "prefers-color-scheme: light"

## Accessibility
- Toggle button has proper ARIA labels: `aria-label="Switch to light/dark mode"`
- Tooltip shows current mode action
- High contrast colors maintained in dark mode
- Smooth transitions for users without motion sensitivity concerns

## Future Enhancements
- [ ] Add keyboard shortcut (e.g., Cmd+Shift+D) for theme toggle
- [ ] Add theme selector (auto, light, dark) instead of just toggle
- [ ] Per-component theme customization
- [ ] Theme transition animation options
- [ ] Export theme preference in user profile/settings
- [ ] Theme preview before applying

## Browser localStorage key
- Key: `theme-preference`
- Values: `'light'` or `'dark'`
- Example: `localStorage.getItem('theme-preference')` → `'dark'`

## CSS Classes Used
- `.dark` - Applied to `<html>` element to enable dark mode
- `dark:` prefix - Tailwind utility for dark mode styles
- `.transition-colors` - Smooth color transitions

## Dependencies
- React 19.2.0
- Tailwind CSS 3.x
- Lucide React 0.562.0 (for Sun/Moon icons)
- No additional packages required
