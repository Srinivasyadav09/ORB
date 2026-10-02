import { env } from "../../config/env";

export class ApiError extends Error {
  constructor(message, { status = 0, data = null, url = "" } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    this.url = url;
  }
}

export function getAuthToken() {
  try { return localStorage.getItem(env.authTokenKey); } catch { return null; }
}

export function setAuthToken(token) {
  try {
    if (token) localStorage.setItem(env.authTokenKey, token);
    else localStorage.removeItem(env.authTokenKey);
  } catch { /* Keep requests usable when storage is unavailable. */ }
}

const refreshTokenKey = `${env.authTokenKey}-refresh`;
export function getRefreshToken() {
  try { return localStorage.getItem(refreshTokenKey); } catch { return null; }
}
export function setRefreshToken(token) {
  try {
    if (token) localStorage.setItem(refreshTokenKey, token);
    else localStorage.removeItem(refreshTokenKey);
  } catch { /* Keep requests usable when storage is unavailable. */ }
}

export function setAuthTokens({ access_token, refresh_token } = {}) {
  setAuthToken(access_token);
  setRefreshToken(refresh_token);
}

function makeUrl(path, query) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${env.apiBaseUrl}${normalizedPath}`, window.location.origin);
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  });
  return url;
}

async function readResponse(response, url) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json().catch(() => null) : await response.text().catch(() => "");
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map(item => item?.msg).filter(Boolean).join(" ") || `Request failed with status ${response.status}.`
        : data?.message || data?.error || `Request failed with status ${response.status}.`;
    throw new ApiError(message, { status: response.status, data, url: String(url) });
  }
  return data;
}

let refreshRequest = null;
function clearAuthentication() {
  setAuthToken(null);
  setRefreshToken(null);
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("orb:unauthorized"));
}

async function refreshAccessToken() {
  const refresh_token = getRefreshToken();
  if (!refresh_token) throw new ApiError("No refresh token is available.", { status: 401 });
  const url = makeUrl("/auth/refresh");
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh_token }),
      credentials: "include"
    });
  } catch (error) {
    throw new ApiError(error.message || "Unable to refresh the ORB session.", { url: String(url) });
  }
  const result = await readResponse(response, url);
  if (!result?.access_token || !result?.refresh_token) {
    throw new ApiError("The ORB API returned an invalid refresh response.", { url: String(url) });
  }
  setAuthTokens(result);
  return result.access_token;
}

async function getRefreshedAccessToken() {
  if (!refreshRequest) {
    refreshRequest = refreshAccessToken().catch(error => {
      clearAuthentication();
      throw error;
    }).finally(() => { refreshRequest = null; });
  }
  return refreshRequest;
}

async function send(method, url, body, headers, token) {
  const requestHeaders = new Headers(headers);
  if (token) requestHeaders.set("Authorization", `Bearer ${token}`);
  let payload;
  if (body !== undefined && body instanceof FormData) payload = body;
  else if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
    payload = JSON.stringify(body);
  }
  requestHeaders.set("Accept", "application/json");
  try {
    return await fetch(url, { method, headers: requestHeaders, body: payload, credentials: "include" });
  } catch (error) {
    throw new ApiError(error.message || "Unable to reach the ORB API.", { url: String(url) });
  }
}

async function request(method, path, { body, query, headers = {} } = {}) {
  if (!env.apiBaseUrl) throw new ApiError("VITE_API_BASE_URL is required when mock mode is disabled.");

  const url = makeUrl(path, query);
  const token = getAuthToken();
  let response = await send(method, url, body, headers, token);
  if (response.status === 401 && token && path !== "/auth/login" && path !== "/auth/refresh") {
    try {
      const refreshedToken = await getRefreshedAccessToken();
      response = await send(method, url, body, headers, refreshedToken);
    } catch {
      clearAuthentication();
      throw await readResponse(response, url);
    }
  }
  if (response.status === 401) {
    clearAuthentication();
  }
  return readResponse(response, url);
}

export const apiClient = Object.freeze({
  request,
  get(path, options) { return request("GET", path, options); },
  post(path, body, options = {}) { return request("POST", path, { ...options, body }); },
  put(path, body, options = {}) { return request("PUT", path, { ...options, body }); },
  patch(path, body, options = {}) { return request("PATCH", path, { ...options, body }); },
  delete(path, options) { return request("DELETE", path, options); }
});
