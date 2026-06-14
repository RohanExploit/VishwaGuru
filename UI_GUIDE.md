# Maharashtra MLA Lookup - User Interface Guide

This document provides a visual guide to the Maharashtra MLA lookup feature in the VishwaGuru application.

---

## 📱 User Journey

### Step 1: Home Screen

When users open VishwaGuru, they see three main options:

```
┌─────────────────────────────────────────────────┐
│                                                 │
│              VishwaGuru                         │
│         Civic action, simplified.               │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │       Start an Issue                    │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │       Who is Responsible?               │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │   Find My MLA (Maharashtra)        ✨   │  │  ← NEW FEATURE
│   └─────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**What happens:** User clicks the purple "Find My MLA (Maharashtra)" button.

---

### Step 2: Pincode Input Form

The user is presented with a simple input form:

```
┌─────────────────────────────────────────────────┐
│                                                 │
│        Find Your Maharashtra MLA                │
│                                                 │
│   Enter your 6-digit pincode                    │
│   ┌─────────────────────────────────────────┐  │
│   │  411001                              _  │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   Currently supporting limited pincodes in      │
│   Maharashtra (MVP)                             │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │     Find My Representatives             │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   Cancel                                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

**What happens:** 
- User enters their 6-digit pincode (e.g., 411001)
- Form validates the input (must be exactly 6 digits)
- User clicks "Find My Representatives" button
- API call is made to backend: `GET /api/mh/rep-contacts?pincode=411001`

---

### Step 3: Results Display

After successful lookup, comprehensive information is displayed:

```
┌─────────────────────────────────────────────────┐
│                                                 │
│        Find Your Maharashtra MLA                │
│                                                 │
│   ┌───────────────────────────────────────┐    │
│   │   🏢 Your Location                    │    │
│   │                                       │    │
│   │   Pincode: 411001                     │    │
│   │   District: Pune                      │    │
│   │   Constituency: Kasba Peth            │    │
│   └───────────────────────────────────────┘    │
│                                                 │
│   ┌───────────────────────────────────────┐    │
│   │   👤 Your MLA                         │    │
│   │                                       │    │
│   │   Sample MLA Pune                     │    │
│   │   Party: Sample Party                 │    │
│   │   Phone: 98XXXXXXXX                   │    │
│   │   Email: pune.mla@example.com         │    │
│   │                                       │    │
│   │   ─────────────────────────────────   │    │
│   │                                       │    │
│   │   "Sample MLA Pune represents the     │    │
│   │   Kasba Peth assembly constituency    │    │
│   │   in Pune district, Maharashtra.      │    │
│   │   MLAs handle local issues such as    │    │
│   │   infrastructure, public services,    │    │
│   │   and constituent welfare."           │    │
│   └───────────────────────────────────────┘    │
│                                                 │
│   ┌───────────────────────────────────────┐    │
│   │   📝 File a Grievance                 │    │
│   │                                       │    │
│   │   [ Central CPGRAMS Portal ]          │    │
│   │   [ Maharashtra Aaple Sarkar Portal ] │    │
│   │                                       │    │
│   │   This is an MVP; data may not be     │    │
│   │   fully accurate.                     │    │
│   └───────────────────────────────────────┘    │
│                                                 │
│   Back to Home                                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**What is displayed:**
1. **Location Information** (Purple card)
   - Pincode entered
   - District name
   - Assembly constituency name

2. **MLA Information** (White card with blue header)
   - MLA's full name
   - Political party affiliation
   - Phone number for contact
   - Email address
   - AI-generated description of their role

3. **Grievance Portals** (Green card)
   - Central CPGRAMS Portal button (green)
   - Maharashtra Aaple Sarkar Portal button (orange)
   - Disclaimer about MVP accuracy

---

### Step 4: Error Handling

#### Case A: Unknown Pincode

```
┌─────────────────────────────────────────────────┐
│                                                 │
│        Find Your Maharashtra MLA                │
│                                                 │
│   Enter your 6-digit pincode                    │
│   ┌─────────────────────────────────────────┐  │
│   │  999999                              _  │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   ┌───────────────────────────────────────┐    │
│   │  ⚠️ Unknown pincode for Maharashtra   │    │
│   │     MVP. Currently only supporting    │    │
│   │     limited pincodes.                 │    │
│   └───────────────────────────────────────┘    │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │     Find My Representatives             │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### Case B: Invalid Format

```
┌─────────────────────────────────────────────────┐
│                                                 │
│        Find Your Maharashtra MLA                │
│                                                 │
│   Enter your 6-digit pincode                    │
│   ┌─────────────────────────────────────────┐  │
│   │  12345                               _  │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   Button is disabled (need 6 digits)            │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │   Find My Representatives  [disabled]   │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🎨 Color Scheme

- **Purple** (#9333EA): Primary action color for MLA lookup feature
- **Blue** (#2563EB): General UI elements, info cards
- **Green** (#059669): Success states, grievance portal links
- **Orange** (#EA580C): Maharashtra state portal
- **Red** (#DC2626): Error messages
- **Gray** (#6B7280): Secondary text, hints

---

## 💻 API Flow

### Request Flow:

```
User Input (Pincode)
    ↓
Frontend Validation (6 digits, numeric only)
    ↓
API Call: GET /api/mh/rep-contacts?pincode=411001
    ↓
Backend Validation
    ↓
Pincode → Constituency Lookup
    ↓
Constituency → MLA Lookup
    ↓
Generate AI Description (Optional, via Gemini)
    ↓
Return JSON Response
    ↓
Display Results in UI
```

### API Response Structure:

```json
{
  "pincode": "411001",
  "state": "Maharashtra",
  "district": "Pune",
  "assembly_constituency": "Kasba Peth",
  "mla": {
    "name": "Sample MLA Pune",
    "party": "Sample Party",
    "phone": "98XXXXXXXX",
    "email": "pune.mla@example.com"
  },
  "description": "AI-generated description...",
  "grievance_links": {
    "central_cpgrams": "https://pgportal.gov.in/",
    "maharashtra_portal": "https://aaplesarkar.mahaonline.gov.in/en",
    "note": "This is an MVP; data may not be fully accurate."
  }
}
```

---

## 🎯 Key Features

### 1. Input Validation
- ✅ Real-time validation (6 digits required)
- ✅ Numeric-only input enforcement
- ✅ Button disabled until valid input
- ✅ Clear error messages

### 2. User Feedback
- ✅ Loading states during API call
- ✅ Success confirmation with full details
- ✅ Error messages for invalid/unknown pincodes
- ✅ Helpful hints about MVP limitations

### 3. Accessibility
- ✅ Clear labels and instructions
- ✅ Proper form structure
- ✅ Keyboard navigation support
- ✅ Responsive design (mobile-friendly)

### 4. Action Links
- ✅ Direct links to grievance portals
- ✅ Opens in new tabs (target="_blank")
- ✅ Secure external links (rel="noopener noreferrer")

---

## 📱 Responsive Design

### Desktop View (max-width: 512px container)
- Full-width cards with comfortable padding
- Large, clickable buttons
- Clear information hierarchy

### Mobile View (< 640px)
- Single-column layout
- Touch-friendly button sizes
- Optimized text sizes
- Proper spacing for thumb navigation

---

## 🔄 State Management

The component manages several states:

1. **view**: Current screen ('home', 'mh-rep', etc.)
2. **maharashtraRepInfo**: Stores API response data
3. **pincode**: User input value
4. **loading**: Shows loading indicator
5. **error**: Displays error messages

---

## 🚀 Future Enhancements

### Phase 2:
- 🔜 Add all Maharashtra pincodes
- 🔜 Real MLA data from official sources
- 🔜 Auto-detect location via GPS
- 🔜 Save recent searches

### Phase 3:
- 🔜 Add MP (Member of Parliament) lookup
- 🔜 Include municipal councillor information
- 🔜 Show constituency boundaries on map
- 🔜 Track MLA's recent activities

---

## 📊 User Experience Metrics

**Expected User Flow:**
1. Click button: 1 action
2. Enter pincode: 6 keystrokes
3. Click find: 1 action
4. View results: Immediate

**Total Actions:** 2 clicks + 6 keystrokes = **~5 seconds to result**

**Success Indicators:**
- ✅ Clear call-to-action
- ✅ Minimal steps required
- ✅ Fast response time
- ✅ Actionable next steps (grievance portals)

---

## 🎓 User Education

The UI includes helpful hints:
- "Currently supporting limited pincodes in Maharashtra (MVP)"
- "This is an MVP; data may not be fully accurate."
- AI description explains MLA's role and responsibilities

This sets proper expectations and educates users about:
- MVP nature of the feature
- MLA's responsibilities
- How to file grievances

---

**Version:** 1.0.0 (MVP)  
**Last Updated:** December 2024  
**Status:** ✅ Production Ready
