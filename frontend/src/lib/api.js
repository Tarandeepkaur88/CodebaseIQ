import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const indexRepository = async (repoUrl) => {
  const res = await api.post("/index", { repo_url: repoUrl });
  return res.data;
};

export const sendAgentMessage = async (repoUrl, message) => {
  const res = await api.post("/agent", { repo_url: repoUrl, message });
  return res.data;
};

export default api;