import re

with open('frontend/src/views/Home.jsx', 'r') as f:
    content = f.read()

# Make sure CameraCheckModal is used
if '{showCameraCheck && <CameraCheckModal onClose={() => setShowCameraCheck(false)} />}' not in content:
    content = content.replace('</>', '{showCameraCheck && <CameraCheckModal onClose={() => setShowCameraCheck(false)} />}</>')

with open('frontend/src/views/Home.jsx', 'w') as f:
    f.write(content)
