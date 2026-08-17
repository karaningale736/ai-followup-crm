// API Configuration
const API_BASE_URL = window.ENV?.VITE_API_BASE_URL || 'http://localhost:8000';

// Determine if in production
const isProd = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

// Set API URL based on environment
let API_URL = API_BASE_URL;

if (isProd && typeof RENDER_BACKEND_URL !== 'undefined') {
  API_URL = RENDER_BACKEND_URL;
}

console.log('API_URL:', API_URL);

export { API_URL, isProd };
