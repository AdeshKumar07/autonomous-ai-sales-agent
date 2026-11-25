import axios from "axios";

// Uses relative paths by default so Vite dev proxy and Nginx production proxy
// both route /api/* and /health cleanly without exposing internal Docker hostnames.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export default api;
