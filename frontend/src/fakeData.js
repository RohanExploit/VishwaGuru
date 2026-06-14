// Fake Data for Fallback Mechanism

export const fakeRecentIssues = [
  {
    id: 1,
    category: "road",
    upvotes: 12,
    created_at: new Date().toISOString(),
    description: "Deep pothole near the main market entrance causing traffic jams."
  },
  {
    id: 2,
    category: "garbage",
    upvotes: 8,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    description: "Garbage not collected for 3 days at Sector 4 corner."
  },
  {
    id: 3,
    category: "streetlight",
    upvotes: 5,
    created_at: new Date(Date.now() - 172800000).toISOString(),
    description: "Streetlights not working on the jogging track."
  }
];

export const fakeResponsibilityMap = {
  "road": {
    "authority": "Municipal Corporation - Engineering Dept",
    "description": "Responsible for road maintenance and pothole repairs."
  },
  "water": {
    "authority": "Water Supply Department",
    "description": "Handles water supply, pipe leakage, and contamination issues."
  },
  "garbage": {
    "authority": "Sanitation Department",
    "description": "Manages waste collection, street sweeping, and dumping grounds."
  },
  "streetlight": {
    "authority": "Electricity Board / Municipal Electrical Dept",
    "description": "Maintains street lights and electrical infrastructure."
  }
};

export const fakeRepInfo = {
  pincode: "411001",
  district: "Pune",
  assembly_constituency: "Pune Cantonment",
  mla: {
    name: "Sunil Kamble",
    party: "BJP",
    phone: "020-26334455",
    email: "sunil.kamble@example.com",
    twitter: "@SunilKambleBJP"
  },
  grievance_links: {
    central_cpgrams: "https://pgportal.gov.in",
    maharashtra_portal: "https://aaplesarkar.mahaonline.gov.in",
    note: "These links are for demo purposes."
  },
  description: "This is sample data because the server could not be reached."
};

export const fakeActionPlan = {
  whatsapp: "Respected Sir/Madam, I would like to report an issue in our area regarding [Issue]. Please look into it.",
  email_subject: "Urgent: Issue Report regarding [Issue]",
  email_body: "Respected Authority,\n\nI am writing to bring to your attention a pressing issue in our locality..."
};
