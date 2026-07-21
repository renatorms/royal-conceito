import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL,
  withCredentials: true,
});

const UNSAFE_METHODS = ["post", "put", "patch", "delete"];

function getCookie(name) {
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)")
  );
  return match ? decodeURIComponent(match[1]) : null;
}

api.interceptors.request.use((config) => {
  if (UNSAFE_METHODS.includes((config.method || "").toLowerCase())) {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    }
  }
  return config;
});

let isRefreshing = false;
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;

    const isRefreshCall = config?.url?.includes("/token/refresh/");

    if (response?.status === 401 && !config._retry && !isRefreshCall) {
      config._retry = true;

      try {
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = api
            .post("/token/refresh/")
            .finally(() => {
              isRefreshing = false;
            });
        }
        await refreshPromise;
        return api(config);
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
