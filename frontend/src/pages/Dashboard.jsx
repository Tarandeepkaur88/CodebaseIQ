import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Code2,
  Plus,
  Menu,
  X,
  Send,
  Loader2,
  FileCode,
  Bug,
  BookOpen,
  MessageSquare,
  ChevronRight,
} from "lucide-react";
import { indexRepository, sendAgentMessage } from "../lib/api";
import { saveRepo, getUserRepos, saveMessage, getChatHistory } from "../lib/supabase";

const intentConfig = {
  qa: { icon: MessageSquare, color: "text-blue-400", bg: "bg-blue-500/10", label: "Q&A" },
  bug: { icon: Bug, color: "text-red-400", bg: "bg-red-500/10", label: "Bug Finder" },
  docs: { icon: BookOpen, color: "text-green-400", bg: "bg-green-500/10", label: "Docs" },
};

export default function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [repos, setRepos] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [repoInput, setRepoInput] = useState("");
  const [indexing, setIndexing] = useState(false);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load saved repos when the dashboard first opens
  useEffect(() => {
    const loadRepos = async () => {
      const savedRepos = await getUserRepos();
      setRepos(savedRepos.map((r) => ({ url: r.repo_url, chunks: r.chunks_count })));
    };
    loadRepos();
  }, []);

  const handleIndexRepo = async (e) => {
    e.preventDefault();
    if (!repoInput.trim()) return;
    setIndexing(true);
    try {
      const result = await indexRepository(repoInput);
      await saveRepo(repoInput, result.chunks_indexed);
      const newRepo = { url: repoInput, chunks: result.chunks_indexed };
      setRepos((prev) => [newRepo, ...prev]);
      setActiveRepo(newRepo);
      setMessages([]);
      setRepoInput("");
    } catch (err) {
      alert("Failed to index repo: " + (err.response?.data?.detail || err.message));
    } finally {
      setIndexing(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !activeRepo) return;

    const userMessage = { role: "user", text: chatInput };
    setMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setSending(true);

    await saveMessage(activeRepo.url, "user", userMessage.text);

    try {
      const result = await sendAgentMessage(activeRepo.url, userMessage.text);
      const answerText =
        result.result?.answer || result.result?.analysis || result.result?.documentation || "No response.";
      const sources = result.result?.sources || [];

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: answerText, intent: result.intent, sources },
      ]);

      await saveMessage(activeRepo.url, "assistant", answerText, result.intent, sources);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Something went wrong. Please try again.", error: true },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleSelectRepo = async (repo) => {
    setActiveRepo(repo);
    const history = await getChatHistory(repo.url);
    setMessages(
      history.map((h) => ({
        role: h.role,
        text: h.message,
        intent: h.intent,
        sources: h.sources,
      }))
    );
  };

  return (
    <div className="h-screen w-full bg-[#0a0a0f] flex overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="w-72 shrink-0 bg-white/[0.02] border-r border-white/10 flex flex-col fixed md:relative h-full z-30"
          >
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Code2 className="w-4 h-4 text-white" />
                </div>
                <span className="text-white font-semibold text-sm">CodebaseIQ</span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-500 hover:text-white transition-colors md:hidden"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleIndexRepo} className="p-4 border-b border-white/10 space-y-2">
              <input
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="Paste GitHub repo URL..."
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-xs placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
              />
              <button
                type="submit"
                disabled={indexing}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xs font-medium py-2 rounded-lg flex items-center justify-center gap-1.5 disabled:opacity-50 transition-opacity"
              >
                {indexing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Indexing...
                  </>
                ) : (
                  <>
                    <Plus className="w-3.5 h-3.5" /> Index Repository
                  </>
                )}
              </button>
            </form>

            <div className="flex-1 overflow-y-auto p-2">
              <p className="text-[10px] uppercase tracking-wider text-gray-500 px-2 py-2 font-medium">
                Indexed Repos
              </p>
              {repos.length === 0 && (
                <p className="text-xs text-gray-600 px-2 py-4 text-center">
                  No repos indexed yet
                </p>
              )}
              {repos.map((repo, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  onClick={() => handleSelectRepo(repo)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg mb-1 flex items-center gap-2 text-xs transition-colors ${
                    activeRepo?.url === repo.url
                      ? "bg-blue-500/10 text-blue-300 border border-blue-500/30"
                      : "text-gray-400 hover:bg-white/5 border border-transparent"
                  }`}
                >
                  <FileCode className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{repo.url.split("/").slice(-2).join("/")}</span>
                </motion.button>
              ))}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="h-14 border-b border-white/10 flex items-center px-4 gap-3 shrink-0">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <div className="flex items-center gap-2 text-sm text-gray-300 min-w-0">
            {activeRepo ? (
              <>
                <FileCode className="w-4 h-4 text-blue-400 shrink-0" />
                <span className="truncate">{activeRepo.url.split("/").slice(-2).join("/")}</span>
              </>
            ) : (
              <span className="text-gray-500">No repository selected</span>
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {!activeRepo && (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
                <Code2 className="w-6 h-6 text-gray-500" />
              </div>
              <h2 className="text-white font-medium mb-1">Index a repository to get started</h2>
              <p className="text-sm text-gray-500 max-w-sm">
                Paste any public GitHub URL in the sidebar, then ask questions, find bugs,
                or generate documentation.
              </p>
            </div>
          )}

          {activeRepo && messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <p className="text-sm text-gray-500 mb-3">Try asking:</p>
              <div className="flex flex-col gap-2 text-xs">
                {[
                  "What does this project do?",
                  "Are there any bugs or security issues?",
                  "Generate documentation for the main functions",
                ].map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => setChatInput(suggestion)}
                    className="text-gray-400 hover:text-blue-400 bg-white/[0.03] hover:bg-white/5 px-4 py-2 rounded-lg transition-colors border border-white/5"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="max-w-2xl mx-auto space-y-4">
            {messages.map((msg, i) => {
              const config = msg.intent ? intentConfig[msg.intent] : null;
              const Icon = config?.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                      msg.role === "user"
                        ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white"
                        : "bg-white/[0.03] border border-white/10 text-gray-200"
                    }`}
                  >
                    {config && (
                      <div className={`inline-flex items-center gap-1.5 ${config.bg} ${config.color} text-[10px] font-medium px-2 py-1 rounded-full mb-2`}>
                        <Icon className="w-3 h-3" />
                        {config.label}
                      </div>
                    )}
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>

                    {msg.sources?.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-1.5">
                        {msg.sources.map((s, si) => (
                          <span
                            key={si}
                            className="text-[10px] bg-white/5 text-gray-400 px-2 py-1 rounded-md flex items-center gap-1"
                          >
                            <FileCode className="w-2.5 h-2.5" />
                            {s.file}
                            {s.start_line && `:${s.start_line}-${s.end_line}`}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}

            {sending && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                <div className="bg-white/[0.03] border border-white/10 rounded-2xl px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                  <span className="text-xs text-gray-400">Thinking...</span>
                </div>
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-white/10 p-4 shrink-0">
          <form onSubmit={handleSendMessage} className="max-w-2xl mx-auto flex items-center gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={activeRepo ? "Ask anything about this codebase..." : "Index a repo first..."}
              disabled={!activeRepo || sending}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 transition-all"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={!activeRepo || sending || !chatInput.trim()}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-2.5 rounded-xl disabled:opacity-40 transition-opacity"
            >
              <Send className="w-4 h-4" />
            </motion.button>
          </form>
        </div>
      </div>
    </div>
  );
}