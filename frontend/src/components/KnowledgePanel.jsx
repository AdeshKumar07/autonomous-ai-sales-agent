import { BookOpen, Database, FileText, RefreshCw, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  fetchKnowledgeDocuments,
  fetchKnowledgeStatus,
  ingestKnowledgeDocuments,
  searchKnowledgeBase,
} from "../services/knowledgeService";

function KnowledgePanel() {
  const [summary, setSummary] = useState(null);
  const [kbStatus, setKbStatus] = useState(null);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [ingestMessage, setIngestMessage] = useState("");
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [error, setError] = useState("");

  const loadKnowledgeState = useCallback(async () => {
    setLoadingDocs(true);
    setError("");
    try {
      const [docsData, statusData] = await Promise.all([
        fetchKnowledgeDocuments(),
        fetchKnowledgeStatus(),
      ]);
      setSummary(docsData);
      setKbStatus(statusData);
    } catch {
      setError("Unable to load knowledge base status.");
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([fetchKnowledgeDocuments(), fetchKnowledgeStatus()])
      .then(([docsData, statusData]) => {
        if (!active) return;
        setSummary(docsData);
        setKbStatus(statusData);
      })
      .catch(() => {
        if (active) setError("Unable to load knowledge base status.");
      })
      .finally(() => {
        if (active) setLoadingDocs(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleIngest = async () => {
    setIngesting(true);
    setError("");
    setIngestMessage("");
    try {
      const res = await ingestKnowledgeDocuments(false);
      setIngestMessage(
        `Ingested ${res.ingested_documents}, updated ${res.updated_documents}, skipped ${res.skipped_documents} duplicates.`
      );
      await loadKnowledgeState();
    } catch {
      setError("Knowledge ingestion failed. Check backend connection.");
    } finally {
      setIngesting(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    const cleaned = query.trim();
    if (!cleaned) return;
    setSearching(true);
    setError("");
    try {
      const data = await searchKnowledgeBase(cleaned, 3);
      setSearchResults(data.results || []);
    } catch {
      setError("Semantic search failed.");
    } finally {
      setSearching(false);
    }
  };

  const isReady = kbStatus?.chromadb_connected && kbStatus?.status === "ready";

  return (
    <div className="p-4 lg:p-5 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen className="h-4 w-4 shrink-0 text-indigo-600" />
          <h2 className="truncate text-sm font-semibold text-slate-900">Knowledge Base</h2>
        </div>
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
            isReady
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : "border-amber-200 bg-amber-50 text-amber-700"
          }`}
        >
          {loadingDocs ? "Checking" : isReady ? "ChromaDB Ready" : kbStatus?.status || "Offline"}
        </span>
      </div>

      <button
        type="button"
        onClick={handleIngest}
        disabled={ingesting}
        className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 transition-colors hover:bg-indigo-100 disabled:opacity-50"
      >
        <RefreshCw className={`h-3.5 w-3.5 ${ingesting ? "animate-spin" : ""}`} />
        <span>{ingesting ? "Ingesting Knowledge Base..." : "Ingest Knowledge Base"}</span>
      </button>

      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      {ingestMessage && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          {ingestMessage}
        </p>
      )}

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <p className="text-[11px] uppercase tracking-wide text-slate-400">Documents</p>
          <p className="mt-0.5 text-sm font-semibold text-slate-800">
            {loadingDocs ? "..." : summary?.total_documents ?? 0}
          </p>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <p className="text-[11px] uppercase tracking-wide text-slate-400">Chunks</p>
          <p className="mt-0.5 text-sm font-semibold text-slate-800">
            {loadingDocs ? "..." : summary?.total_chunks ?? 0}
          </p>
        </div>
      </div>

      <div>
        <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          <Database className="h-3.5 w-3.5" />
          <span>Indexed Documents</span>
        </p>
        {summary?.documents?.length ? (
          <ul className="space-y-1.5">
            {summary.documents.map((doc) => (
              <li
                key={doc.source_filename}
                className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/70 px-2.5 py-1.5 text-xs"
              >
                <span className="flex items-center gap-1.5 truncate font-medium text-slate-700">
                  <FileText className="h-3.5 w-3.5 shrink-0 text-indigo-500" />
                  <span className="truncate">{doc.source_filename}</span>
                </span>
                <span className="shrink-0 rounded bg-white px-1.5 py-0.5 text-[10px] text-slate-500 border border-slate-200">
                  {doc.chunk_count} chunks
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-slate-400">No documents indexed yet.</p>
        )}
      </div>

      <form onSubmit={handleSearch} className="space-y-2">
        <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          Test Retrieval Search
        </label>
        <div className="flex gap-1.5">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search company, pricing, policy..."
            className="flex-1 min-w-0 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:bg-white focus:outline-none"
          />
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            <Search className="h-3.5 w-3.5" />
          </button>
        </div>
      </form>

      {searchResults.length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Retrieved Chunks
          </p>
          {searchResults.map((chunk) => (
            <div
              key={chunk.chunk_id}
              className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-2.5 text-xs"
            >
              <div className="flex items-center justify-between gap-2 font-medium text-indigo-800">
                <span className="truncate">
                  {chunk.source_filename} ({chunk.document_type})
                </span>
                <span className="shrink-0 text-[10px]">score {chunk.score}</span>
              </div>
              <p className="mt-1 line-clamp-3 text-[11px] leading-relaxed text-slate-600">
                {chunk.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default KnowledgePanel;
