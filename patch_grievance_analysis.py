import re

with open("frontend/src/views/GrievanceAnalysis.jsx", "r") as f:
    content = f.read()

# Change the endpoint from /api/classify-grievance to /api/hf/generate
# Since /api/hf/generate expects a prompt, max_new_tokens, temperature
# We will construct a prompt asking it to classify the grievance

new_fetch_logic = """
      const prompt = `Classify the following public grievance into one of these departments: Road Maintenance, Waste Management, Electricity, Water Supply, Public Safety, or Other. Respond with ONLY the department name.\\n\\nGrievance: ${text}\\n\\nDepartment:`;
      const response = await fetch(`${API_URL}/api/hf/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          max_new_tokens: 10,
          temperature: 0.1
        }),
      });

      if (!response.ok) {
        throw new Error('Classification failed');
      }

      const data = await response.json();
      setResult(data.text.trim());
"""

# Replace the old fetch logic
pattern = re.compile(
    r"const response = await fetch\(`\$\{API_URL\}/api/classify-grievance`.*?setResult\(data\.category\);",
    re.DOTALL
)

content = pattern.sub(new_fetch_logic.strip(), content)

with open("frontend/src/views/GrievanceAnalysis.jsx", "w") as f:
    f.write(content)
