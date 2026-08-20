// The API base URL is read from the <meta name="api-base-url"> tag in
// index.html — change it there, not here, if the backend runs elsewhere.
const API_BASE_URL =
  document.querySelector('meta[name="api-base-url"]')?.content ||
  "http://localhost:8000/api";
