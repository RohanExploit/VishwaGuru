import re

with open('frontend/src/views/Home.jsx', 'r') as f:
    content = f.read()

emotion_button = """
            <motion.button
              whileHover={{ scale: 1.02, x: 5 }}
              onClick={() => navigate('/emotion')}
              className="w-full flex items-center gap-6 bg-purple-600 rounded-[2rem] p-8 text-white shadow-2xl shadow-purple-500/20 group overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
              <div className="p-4 bg-white/20 rounded-2xl">
                <Eye size={28} />
              </div>
              <div className="text-left">
                <span className="block text-xl font-black leading-tight">Emotion Detector</span>
                <span className="text-[10px] font-black uppercase tracking-widest opacity-80 mt-1 block">HF AI Integration</span>
              </div>
            </motion.button>
"""

if "Emotion Detector" not in content:
    content = content.replace(
        '<h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.3em] px-2 mb-2">Auxiliary Systems</h3>',
        '<h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.3em] px-2 mb-2">Auxiliary Systems</h3>' + emotion_button
    )

with open('frontend/src/views/Home.jsx', 'w') as f:
    f.write(content)
