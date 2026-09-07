export default {
  process(src) {
    // Replace import.meta.env with a mock object
    return src.replace(/import\.meta\.env/g, '({ VITE_API_URL: "http://localhost:3000" })');
  }
};