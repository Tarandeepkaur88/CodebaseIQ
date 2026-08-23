import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// ---- Repos ----

export const saveRepo = async (repoUrl, chunksCount) => {
  const { data: userData } = await supabase.auth.getUser();
  const user = userData?.user;
  if (!user) return null;

  const { data, error } = await supabase
    .from("repos")
    .insert({ user_id: user.id, repo_url: repoUrl, chunks_count: chunksCount })
    .select()
    .single();

  if (error) console.error("Failed to save repo:", error);
  return data;
};

export const getUserRepos = async () => {
  const { data, error } = await supabase
    .from("repos")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Failed to fetch repos:", error);
    return [];
  }
  return data;
};

// ---- Chat History ----

export const saveMessage = async (repoUrl, role, message, intent = null, sources = null) => {
  const { data: userData } = await supabase.auth.getUser();
  const user = userData?.user;
  if (!user) return null;

  const { data, error } = await supabase
    .from("chat_history")
    .insert({
      user_id: user.id,
      repo_url: repoUrl,
      role,
      message,
      intent,
      sources,
    })
    .select()
    .single();

  if (error) console.error("Failed to save message:", error);
  return data;
};

export const getChatHistory = async (repoUrl) => {
  const { data, error } = await supabase
    .from("chat_history")
    .select("*")
    .eq("repo_url", repoUrl)
    .order("created_at", { ascending: true });

  if (error) {
    console.error("Failed to fetch chat history:", error);
    return [];
  }
  return data;
};