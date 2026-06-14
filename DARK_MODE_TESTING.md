# Dark Mode Testing Guide

## Test Coverage for Dark Mode Implementation

This guide covers all aspects of testing the dark mode feature implementation.

---

## Manual Testing Checklist

### 1. Theme Toggle Functionality

#### Test 1.1: Basic Toggle
- [ ] Load the application
- [ ] Locate the Sun/Moon icon in the top-right corner of the header
- [ ] Click the toggle button
- [ ] Verify theme switches from light to dark
- [ ] Click again and verify it switches back to light
- [ ] **Expected**: Smooth transition with no visual glitches

#### Test 1.2: Toggle Visibility
- [ ] Verify toggle button is visible on all screen sizes (mobile, tablet, desktop)
- [ ] Check button positioning in header (top-right area)
- [ ] Verify icon changes from Sun to Moon and vice versa
- [ ] Verify button styling matches design (proper colors and hover effects)

#### Test 1.3: Toggle Responsiveness
- [ ] Click toggle multiple times rapidly
- [ ] Verify no console errors appear
- [ ] Verify theme changes reliably every time

### 2. Theme Persistence

#### Test 2.1: localStorage Saving
- [ ] Open browser DevTools (F12)
- [ ] Go to Application > Local Storage
- [ ] Set light mode, check `theme-preference` key exists with value `'light'`
- [ ] Set dark mode, check `theme-preference` key exists with value `'dark'`
- [ ] **Expected**: localStorage updated correctly

#### Test 2.2: Persistence Across Reloads
- [ ] Set theme to dark mode
- [ ] Reload page (F5 or Cmd+R)
- [ ] Verify theme remains dark
- [ ] Set theme to light mode
- [ ] Reload page
- [ ] Verify theme remains light
- [ ] Verify toggle button icon correctly reflects current theme

#### Test 2.3: Persistence Across Tabs
- [ ] Open application in current tab in dark mode
- [ ] Open same application URL in new tab
- [ ] Verify new tab also opens in dark mode
- [ ] Change theme in new tab
- [ ] Refresh first tab
- [ ] Verify first tab reflects the new theme

#### Test 2.4: Persistence Across Sessions
- [ ] Set theme to dark mode
- [ ] Close browser completely
- [ ] Reopen browser and navigate to application
- [ ] Verify theme is still dark mode

### 3. System Preference Detection

#### Test 3.1: System Dark Mode Preference
- [ ] Set your OS to dark mode
- [ ] Clear localStorage (open DevTools > Application > Local Storage > Clear All)
- [ ] Refresh application
- [ ] Verify application opens in dark mode
- [ ] **Expected**: Respects OS dark mode setting

#### Test 3.2: System Light Mode Preference
- [ ] Set your OS to light mode
- [ ] Clear localStorage
- [ ] Refresh application
- [ ] Verify application opens in light mode

#### Test 3.3: System Preference Override
- [ ] Set OS to dark mode
- [ ] Clear localStorage
- [ ] Refresh application (should be dark)
- [ ] Click toggle to switch to light mode
- [ ] Change OS to light mode
- [ ] Refresh application
- [ ] Verify application stays in light mode (user preference overrides system)

#### Test 3.4: System Theme Change Detection
- [ ] On supported browsers (Chrome, Edge), use DevTools to emulate theme change:
  - [ ] Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
  - [ ] Search for "Emulate CSS media"
  - [ ] Select different prefers-color-scheme options
  - [ ] Verify application responds (if no user preference set)

### 4. UI/UX Testing

#### Test 4.1: Visual Consistency - Light Mode
- [ ] Verify all text is readable (good contrast)
- [ ] Check all buttons are visible and styled properly
- [ ] Verify card backgrounds are light with proper shadows
- [ ] Check border colors are appropriate for light theme
- [ ] Verify no dark colors that clash with light mode

#### Test 4.2: Visual Consistency - Dark Mode
- [ ] Verify all text is readable on dark backgrounds
- [ ] Check all buttons have proper contrast in dark mode
- [ ] Verify card backgrounds are dark with appropriate shadows
- [ ] Check border colors work in dark theme
- [ ] Verify gradient elements remain visible

#### Test 4.3: Component Styling
- [ ] Navigation/Header: Check styling in both modes
- [ ] Cards and containers: Verify backgrounds and borders
- [ ] Buttons: Check hover states in both modes
- [ ] Forms (if present): Verify input fields are styled correctly
- [ ] Links: Check hover colors in both modes
- [ ] Modals/Alerts: Verify readability and styling
- [ ] Footer: Verify styling in both modes

#### Test 4.4: Smooth Transitions
- [ ] Toggle theme
- [ ] Observe color transitions are smooth (should be 300ms)
- [ ] Verify no jarring color changes or flashing
- [ ] Check background elements animate smoothly

### 5. Browser Compatibility

#### Test 5.1: Desktop Browsers
- [ ] **Chrome/Edge**: Latest version
  - [ ] Toggle works
  - [ ] localStorage persists
  - [ ] Styles render correctly
- [ ] **Firefox**: Latest version
  - [ ] Toggle works
  - [ ] localStorage persists
  - [ ] Styles render correctly
- [ ] **Safari**: Latest version
  - [ ] Toggle works
  - [ ] localStorage persists
  - [ ] Styles render correctly

#### Test 5.2: Mobile Browsers
- [ ] **Chrome Mobile**: Latest version
  - [ ] Toggle accessible and clickable
  - [ ] Theme persists
  - [ ] Responsive layout maintained
- [ ] **Safari iOS**: Latest version
  - [ ] Toggle accessible
  - [ ] Theme persists
  - [ ] Layout is responsive
- [ ] **Firefox Mobile**: Latest version
  - [ ] Toggle works
  - [ ] Theme persists

#### Test 5.3: Responsive Design
- [ ] Test on 320px width (mobile)
- [ ] Test on 768px width (tablet)
- [ ] Test on 1024px+ width (desktop)
- [ ] Verify toggle button is visible and clickable at all sizes
- [ ] Verify layout adapts properly in dark/light modes at each size

### 6. Edge Cases and Error Handling

#### Test 6.1: localStorage Disabled
- [ ] Disable localStorage in browser settings
- [ ] Refresh application
- [ ] Toggle theme
- [ ] Verify application still works (theme resets on reload, which is acceptable)

#### Test 6.2: No JavaScript
- [ ] Test with JavaScript disabled
- [ ] Verify application shows appropriate fallback (may not have theme toggle)

#### Test 6.3: Rapid Theme Switching
- [ ] Click toggle 10+ times rapidly
- [ ] Verify no errors or performance degradation
- [ ] Verify final theme is correct

#### Test 6.4: Mixed Content
- [ ] Verify external images load properly in both themes
- [ ] Check embedded content (videos, iframes) work in both modes

### 7. Accessibility Testing

#### Test 7.1: ARIA Labels
- [ ] Use screen reader (VoiceOver on Mac, NVDA on Windows)
- [ ] Tab to theme toggle button
- [ ] Verify screen reader announces: "Switch to light/dark mode"
- [ ] Verify button description is announced

#### Test 7.2: Keyboard Navigation
- [ ] Tab to toggle button
- [ ] Press Enter/Space to toggle theme
- [ ] Verify theme changes with keyboard input

#### Test 7.3: Color Contrast
- [ ] Use contrast checker tool (WebAIM, Axe)
- [ ] Verify all text meets WCAG AA standards in both modes
- [ ] Verify buttons meet contrast requirements

#### Test 7.4: Focus Indicators
- [ ] Tab to toggle button
- [ ] Verify visible focus ring around button
- [ ] Verify focus ring is visible in both light and dark modes

### 8. Performance Testing

#### Test 8.1: Load Time
- [ ] Clear cache
- [ ] Load application
- [ ] Verify toggle button appears quickly
- [ ] Measure no significant performance impact

#### Test 8.2: Memory Usage
- [ ] Open DevTools > Memory
- [ ] Take heap snapshot before theme toggle
- [ ] Toggle theme 20+ times
- [ ] Take another heap snapshot
- [ ] Verify no significant memory leak

#### Test 8.3: CPU/Rendering Performance
- [ ] Open DevTools > Performance
- [ ] Record while toggling theme
- [ ] Verify smooth 60fps transitions
- [ ] Check no long tasks blocking main thread

---

## Automated Testing (For Developers)

### Unit Tests for ThemeContext

```javascript
describe('ThemeContext', () => {
  test('should initialize with localStorage preference', () => {
    // Test that saved preference is loaded
  });
  
  test('should initialize with system preference', () => {
    // Test system preference detection
  });
  
  test('should toggle theme correctly', () => {
    // Test toggleTheme function
  });
  
  test('should persist theme to localStorage', () => {
    // Test localStorage update
  });
  
  test('should respond to system theme changes', () => {
    // Test media query listener
  });
});
```

### Integration Tests

```javascript
describe('Dark Mode Integration', () => {
  test('should apply dark class to html element', () => {
    // Test DOM class application
  });
  
  test('should update all component styles', () => {
    // Test CSS dark mode styles apply
  });
  
  test('should persist across route changes', () => {
    // Test theme persists in SPA navigation
  });
});
```

---

## Bug Tracking Template

When reporting issues, use this template:

```
**Title**: [Dark Mode] Brief description

**Browser**: [Chrome/Firefox/Safari] Version X.X

**OS**: [macOS/Windows/Linux] Version

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:

**Actual Behavior**:

**Screenshots**: [if applicable]

**Console Errors**: [if any]

**localStorage State**: [share theme-preference value]
```

---

## Sign-Off Checklist

- [ ] All manual tests passed
- [ ] No console errors
- [ ] localStorage working correctly
- [ ] System preference detection working
- [ ] All browsers compatible
- [ ] Responsive design maintained
- [ ] Accessibility standards met
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Ready for production

---

## Notes

- Test on real devices when possible, not just emulators
- Clear cache between tests to ensure fresh state
- Test with both JavaScript enabled and disabled
- Verify no console warnings or errors
- Test with network throttling (if applicable)

---

**Last Updated**: February 9, 2026
**Tested By**: [Your Name]
**Test Date**: [Date]
