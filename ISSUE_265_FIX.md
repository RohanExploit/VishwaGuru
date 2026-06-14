# Fix for Issue #265: Case Sensitivity Issue in Clone Instructions

## Problem Description
The README.md installation section used "cd vishwaguru" after cloning, but the actual repository name is "VishwaGuru" (with capital V and G). While this works on case-insensitive file systems like Windows, it could cause issues on Linux/macOS systems and should be corrected for consistency.

## Changes Made

### Files Modified
- `README.md` (2 instances updated)

### Specific Changes

#### 1. First Installation Section (Line ~149)
**Before:**
```bash
git clone https://github.com/Ewocs/VishwaGuru.git
cd vishwaguru
```

**After:**
```bash
git clone https://github.com/Ewocs/VishwaGuru.git
cd VishwaGuru
```

#### 2. Second Installation Section (Line ~378)
**Before:**
```bash
git clone https://github.com/Ewocs/VishwaGuru.git
cd vishwaguru
```

**After:**
```bash
git clone https://github.com/Ewocs/VishwaGuru.git
cd VishwaGuru
```

## Validation
- The repository name "VishwaGuru" matches the actual directory name
- This ensures cross-platform compatibility (Linux/macOS are case-sensitive)
- No other references to lowercase "vishwaguru" were found in the codebase

## Impact
- Eliminates potential setup issues for contributors on case-sensitive file systems
- Improves documentation consistency and reliability
- No breaking changes to existing functionality

## Commit Details
- Branch: `read-2`
- Files changed: 1
- Lines changed: 2 insertions, 2 deletions</content>
<parameter name="filePath">c:\Users\Gupta\Downloads\VishwaGuru\ISSUE_265_FIX.md