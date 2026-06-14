# Dark Mode Feature - Quick Start Guide

## What's New? 🌙

VishwaGuru now includes a full dark mode implementation! Users can toggle between light and dark themes with one click, and their preference is automatically saved.

## Features

✅ **One-Click Toggle** - Dark mode button in the header navbar
✅ **Persistent** - Theme preference saved in localStorage
✅ **System-Aware** - Respects your OS dark mode preference
✅ **Smooth Transitions** - Elegant theme switching with CSS transitions
✅ **Fully Styled** - All UI components support dark mode
✅ **Accessible** - ARIA labels and keyboard friendly

## How to Use

### Toggle Dark Mode
1. Look for the **Sun/Moon icon** in the top-right corner of the header
2. Click to switch between light and dark themes
3. Your preference is automatically saved

### Your Theme Will Persist
- The selected theme will be remembered across page reloads
- Works across all browser tabs and sessions
- You can change it anytime by clicking the toggle again

### System Preference
- If you haven't selected a preference, VishwaGuru uses your OS dark mode setting
- Once you click the toggle, your choice takes priority
- To reset to system preference, you can clear localStorage

## What Gets Affected

The dark mode styling applies to:
- ✓ Background colors
- ✓ Text colors
- ✓ Card and component backgrounds
- ✓ Border colors
- ✓ Shadows and effects
- ✓ All UI elements

## Browser Compatibility

Dark mode works on all modern browsers:
- Chrome/Edge 76+
- Firefox 67+
- Safari 12.1+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Customization for Developers

### Add Dark Mode to Your Components

If you're building new components, use Tailwind's `dark:` prefix:

```jsx
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  Your content
</div>
```

### Access Theme in Code

```jsx
import { useTheme } from './contexts/ThemeContext';

function MyComponent() {
  const { isDark, toggleTheme } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      Current mode: {isDark ? 'Dark' : 'Light'}
    </button>
  );
}
```

## Technical Details

- **Theme Context**: `src/contexts/ThemeContext.jsx`
- **Toggle Component**: `src/components/DarkModeToggle.jsx`
- **Configuration**: `tailwind.config.js` (darkMode: 'class')
- **Storage Key**: `theme-preference` in localStorage

## Troubleshooting

**Theme not persisting?**
- Check if localStorage is enabled in your browser
- Clear browser cache and try again

**Dark mode looks incorrect?**
- Ensure you're using the latest version of the app
- Try clearing cache (Cmd+Shift+R or Ctrl+Shift+R)

**Toggle button not visible?**
- Check browser zoom level (should be 100%)
- Ensure JavaScript is enabled

## Color Palette

### Dark Mode Colors
- **Background**: #1a1a1a (primary), #2d2d2d (secondary)
- **Text**: #f3f4f6 (primary), #d1d5db (secondary)
- **Borders**: #404040

### Light Mode Colors
- **Background**: #ffffff (primary), #f9fafb (secondary)
- **Text**: #1f2937 (primary), #6b7280 (secondary)
- **Borders**: #e5e7eb

## Performance

The dark mode implementation is lightweight:
- ✓ No additional dependencies
- ✓ Uses native React Context
- ✓ CSS-based transitions (smooth performance)
- ✓ Minimal JavaScript overhead

## Questions or Issues?

If you encounter any problems with dark mode:
1. Check the browser console for errors (F12)
2. Verify localStorage is working
3. Try clearing browser cache
4. Report issues on GitHub with details about your setup

Enjoy dark mode! 🎉
