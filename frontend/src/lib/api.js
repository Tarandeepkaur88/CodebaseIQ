import axios from "axios";
import { supabase } from "./supabase";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
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