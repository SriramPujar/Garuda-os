"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getApiUrl } from "@/utils/api";
import { searchYouTubeClient } from "@/utils/spiritual_search";
import { 
  Search, 
  Tv, 
  BookOpen, 
  Play, 
  Compass, 
  Clock, 
  ShieldCheck, 
  FileText, 
  Plus, 
  Trash, 
  MessageSquare, 
  Sliders,
  Globe,
  Activity,
  Network,
  Database,
  Sparkles,
  RefreshCw,
  HelpCircle,
  ExternalLink
} from "lucide-react";

interface Video {
  id?: number;
  youtube_id: string;
  title: string;
  description: string;
  duration: number;
  thumbnail_url: string;
  category: string;
  summary?: string;
  learnings_json?: string;
  timestamps_json?: string;
  authenticity_score?: number;
  spiritual_tradition?: string;
  content_type?: string;
  energy_type?: string;
  speaker_name?: string;
  scriptures_referenced?: string;
  search_score?: number;
}

interface VideoNote {
  id: number;
  timestamp: number;
  note_text: string;
  created_at: string;
}

interface LearningPath {
  id: number;
  name: string;
  description: string;
  category: string;
  level: string;
}

interface GraphNodeData {
  id: string;
  name: string;
  type: string;
  description: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphLinkData {
  source: string;
  target: string;
  type: string;
  weight: number;
}

const STATIC_FALLBACK_VIDEOS: Video[] = [
  {
    id: 1001,
    youtube_id: "aaBeXwSsmtY",
    title: "Who Am I? – Swami Sarvapriyananda (Vedanta Society of New York)",
    description: "An introduction to self-inquiry (Atma-Vichara) as taught by Ramana Maharshi, explained by Swami Sarvapriyananda.",
    duration: 960,
    thumbnail_url: "https://img.youtube.com/vi/aaBeXwSsmtY/0.jpg",
    category: "Vedanta"
  },
  {
    id: 1002,
    youtube_id: "ATflA6WOy0I",
    title: "Vishnu Sahasranamam – M.S. Subbulakshmi",
    description: "The legendary rendering of the 1000 Names of Lord Vishnu by Bharat Ratna M.S. Subbulakshmi.",
    duration: 3120,
    thumbnail_url: "https://img.youtube.com/vi/ATflA6WOy0I/0.jpg",
    category: "Bhakti"
  },
  {
    id: 1003,
    youtube_id: "emsphj4r_Q8",
    title: "Mahamrityunjaya Mantra – 108 Times Healing Chant",
    description: "Sacred Mahamrityunjaya Mantra chanted 108 times for healing, protection, and liberation from the cycle of death.",
    duration: 2400,
    thumbnail_url: "https://img.youtube.com/vi/emsphj4r_Q8/0.jpg",
    category: "Chants"
  },
  {
    id: 1004,
    youtube_id: "hMBKmQEPNzI",
    title: "Shiva Tandava Stotram – Powerful Devotional",
    description: "The powerful Shiva Tandava Stotram, a hymn praising Lord Shiva's cosmic dance.",
    duration: 480,
    thumbnail_url: "https://img.youtube.com/vi/hMBKmQEPNzI/0.jpg",
    category: "Chants"
  },
  {
    id: 1005,
    youtube_id: "ZhIJgYLjoVw",
    title: "Sri Venkateswara Suprabhatam – Morning Prayer",
    description: "Auspicious morning chants praising Lord Venkateswara, sung at dawn to invoke the blessings of the Divine.",
    duration: 1200,
    thumbnail_url: "https://img.youtube.com/vi/ZhIJgYLjoVw/0.jpg",
    category: "Bhakti"
  }
];

const STATIC_LEARNING_PATHS: LearningPath[] = [
  {
    id: 101,
    name: "Vedanta Foundations",
    description: "Learn the core concepts of Non-dualism, Atman, and Brahman from the Upanishads.",
    category: "Vedanta",
    level: "Beginner"
  },
  {
    id: 102,
    name: "Bhakti Yoga & Chanting",
    description: "Discover the significance of sound vibration (Nada) and devotional surrender.",
    category: "Bhakti",
    level: "Intermediate"
  }
];

export default function SpiritualTube() {
  const [searchQuery, setSearchQuery] = useState("");
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(false);
  const [isBackendOffline, setIsBackendOffline] = useState(false);
  const [paths, setPaths] = useState<LearningPath[]>([]);
  const [activeVideo, setActiveVideo] = useState<Video | null>(null);
  const [hasSearched, setHasSearched] = useState(false);  // true after first search attempt
  const [lastQuery, setLastQuery] = useState("");
  
  // Note inputs
  const [noteText, setNoteText] = useState("");
  const [noteTimestamp, setNoteTimestamp] = useState(0);
  const [videoNotes, setVideoNotes] = useState<VideoNote[]>([]);
  
  // AI summary and teachings
  const [aiSummaryLoading, setAiSummaryLoading] = useState(false);
  const [aiTeachings, setAiTeachings] = useState<any>(null);
  
  // Safe Mode settings
  const [safeMode, setSafeMode] = useState(true);
  const [playbackSeconds, setPlaybackSeconds] = useState(0);
  const [showMindfulWarning, setShowMindfulWarning] = useState(false);
  const playbackTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Tabs state
  const [activeTab, setActiveTab] = useState<"feed" | "graph" | "crawl">("feed");

  // Advanced Filters State
  const [showFilters, setShowFilters] = useState(false);
  const [tradition, setTradition] = useState("All");
  const [contentType, setContentType] = useState("All");
  const [energyType, setEnergyType] = useState("All");
  const [minAuthenticity, setMinAuthenticity] = useState(0);
  const [expandMultilingual, setExpandMultilingual] = useState(true);

  // Knowledge Graph State
  const [graphData, setGraphData] = useState<{ nodes: GraphNodeData[]; links: GraphLinkData[] }>({ nodes: [], links: [] });
  const [simulationNodes, setSimulationNodes] = useState<GraphNodeData[]>([]);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNodeData | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  // Crawl Dashboard State
  const [queueStats, setQueueStats] = useState<Record<string, number>>({ pending: 0, processing: 0, completed: 0, failed: 0 });
  const [crawlHistory, setCrawlHistory] = useState<any[]>([]);
  const [newSeedUrl, setNewSeedUrl] = useState("");
  const [newSourceType, setNewSourceType] = useState("youtube_channel");
  const [newPriority, setNewPriority] = useState(0);
  const [seedError, setSeedError] = useState("");
  const [seedSuccess, setSeedSuccess] = useState("");
  const [triggerLoading, setTriggerLoading] = useState(false);

  const [hasYtKey, setHasYtKey] = useState(false);

  useEffect(() => {
    fetchLearningPaths();
    fetchCuratedVideos();
    const localYtKey = typeof window !== "undefined" ? localStorage.getItem("youtube_api_key") : null;
    const clientYtKey = localYtKey || process.env.NEXT_PUBLIC_YOUTUBE_API_KEY || process.env.YOUTUBE_API_KEY;
    setHasYtKey(!!clientYtKey);
  }, []);


  const filterFallbackVideos = (queryText: string) => {
    let filtered = [...STATIC_FALLBACK_VIDEOS];
    if (queryText.trim()) {
      const q = queryText.toLowerCase();
      filtered = filtered.filter(v => 
        v.title.toLowerCase().includes(q) || 
        v.description.toLowerCase().includes(q)
      );
    }
    setVideos(filtered);
  };

  const fetchCuratedVideos = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/videos`);
      if (response.ok) {
        const data = await response.json();
        setVideos(data && data.length > 0 ? data : STATIC_FALLBACK_VIDEOS);
        setIsBackendOffline(false);
      } else {
        setIsBackendOffline(true);
        setVideos(STATIC_FALLBACK_VIDEOS);
      }
    } catch (e) {
      console.error("Backend offline, using fallback videos:", e);
      setIsBackendOffline(true);
      setVideos(STATIC_FALLBACK_VIDEOS);
    }
    setLoading(false);
  };

  const fetchLearningPaths = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/paths`);
      if (response.ok) {
        const data = await response.json();
        setPaths(data && data.length > 0 ? data : STATIC_LEARNING_PATHS);
        setIsBackendOffline(false);
      } else {
        setIsBackendOffline(true);
        setPaths(STATIC_LEARNING_PATHS);
      }
    } catch (e) {
      console.error("Backend offline, using static learning paths:", e);
      setIsBackendOffline(true);
      setPaths(STATIC_LEARNING_PATHS);
    }
  };

  // Hybrid Search logic using advanced discovery router
  const triggerSearch = async (queryText: string, currentTradition?: string, currentContentType?: string, currentEnergy?: string, currentMinAuth?: number, currentExpand?: boolean) => {
    setLoading(true);
    setHasSearched(true);
    setLastQuery(queryText);
    
    // Check if client-side YouTube search is configured
    const localYtKey = typeof window !== "undefined" ? localStorage.getItem("youtube_api_key") : null;
    const clientYtKey = localYtKey || process.env.NEXT_PUBLIC_YOUTUBE_API_KEY || process.env.YOUTUBE_API_KEY;

    try {
      const trad = currentTradition !== undefined ? currentTradition : tradition;
      const ctype = currentContentType !== undefined ? currentContentType : contentType;
      const nrg = currentEnergy !== undefined ? currentEnergy : energyType;
      const minAuth = currentMinAuth !== undefined ? currentMinAuth : minAuthenticity;
      const exp = currentExpand !== undefined ? currentExpand : expandMultilingual;

      let url = `${getApiUrl()}/api/v1/discovery/search/videos?query=${encodeURIComponent(queryText)}`;
      if (trad && trad !== "All") url += `&tradition=${encodeURIComponent(trad)}`;
      if (ctype && ctype !== "All") url += `&content_type=${encodeURIComponent(ctype)}`;
      if (nrg && nrg !== "All") url += `&energy=${encodeURIComponent(nrg)}`;
      if (minAuth > 0) url += `&min_authenticity=${minAuth}`;
      url += `&expand=${exp}`;

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setVideos(data);
        setIsBackendOffline(false);
      } else {
        // Backend API failed. Try client-side live search if API key exists.
        if (clientYtKey) {
          const ytResults = await searchYouTubeClient(queryText, clientYtKey);
          if (ytResults && ytResults.length > 0) {
            setVideos(ytResults);
            setIsBackendOffline(false);
          } else {
            setIsBackendOffline(true);
            filterFallbackVideos(queryText);
          }
        } else {
          setIsBackendOffline(true);
          filterFallbackVideos(queryText);
        }
      }
    } catch (e) {
      console.error("Search API failed, applying client-side fallback filter:", e);
      // Try client-side live search if API key exists.
      if (clientYtKey) {
        try {
          const ytResults = await searchYouTubeClient(queryText, clientYtKey);
          if (ytResults && ytResults.length > 0) {
            setVideos(ytResults);
            setIsBackendOffline(false);
          } else {
            setIsBackendOffline(true);
            filterFallbackVideos(queryText);
          }
        } catch (ytErr) {
          console.error("Client-side YouTube search failed:", ytErr);
          setIsBackendOffline(true);
          filterFallbackVideos(queryText);
        }
      } else {
        setIsBackendOffline(true);
        filterFallbackVideos(queryText);
      }
    }
    setLoading(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    triggerSearch(searchQuery);
  };

  const selectVideo = async (video: Video) => {
    const applyVideoDetails = (details: Video) => {
      setActiveVideo(details);
      
      setPlaybackSeconds(0);
      setShowMindfulWarning(false);
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
      
      if (safeMode) {
        let count = 0;
        playbackTimerRef.current = setInterval(() => {
          count += 1;
          setPlaybackSeconds(count);
          if (count === 30) {
            setShowMindfulWarning(true);
          }
        }, 1000);
      }

      fetchNotes(video.youtube_id);
      
      if (details.learnings_json) {
        try {
          setAiTeachings(JSON.parse(details.learnings_json));
        } catch {
          setAiTeachings(null);
        }
      } else {
        setAiTeachings(null);
      }
    };

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/videos/${video.youtube_id}`);
      if (response.ok) {
        const details = await response.json();
        applyVideoDetails(details);
      } else {
        applyVideoDetails(video);
      }
    } catch (e) {
      console.error("Failed to load video details from backend, falling back to client-side play:", e);
      applyVideoDetails(video);
    }
  };

  const closeVideo = () => {
    setActiveVideo(null);
    if (playbackTimerRef.current) {
      clearInterval(playbackTimerRef.current);
      playbackTimerRef.current = null;
    }
    setShowMindfulWarning(false);
  };

  const fetchNotes = async (ytId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/videos/${ytId}/notes`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setVideoNotes(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const addNote = async () => {
    if (!activeVideo || !noteText.trim()) return;
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/videos/${activeVideo.youtube_id}/notes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          timestamp: noteTimestamp,
          note_text: noteText
        })
      });

      if (response.ok) {
        setNoteText("");
        fetchNotes(activeVideo.youtube_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteNote = async (noteId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/notes/${noteId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (response.ok && activeVideo) {
        fetchNotes(activeVideo.youtube_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const generateAISummary = async () => {
    if (!activeVideo) return;
    setAiSummaryLoading(true);
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/spiritualtube/videos/${activeVideo.youtube_id}/ai-summary`, {
        method: "POST"
      });
      if (response.ok) {
        const data = await response.json();
        setActiveVideo(prev => prev ? { ...prev, summary: data.summary } : null);
        setAiTeachings(data.learnings);
      }
    } catch (e) {
      console.error(e);
    }
    setAiSummaryLoading(false);
  };

  // Knowledge Graph Loader
  const fetchGraphData = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/discovery/graph`);
      if (response.ok) {
        const data = await response.json();
        setGraphData(data);
      }
    } catch (e) {
      console.error("Error loading graph data:", e);
    }
  };

  // Crawl Dashboard Loaders
  const fetchCrawlQueueStatus = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/discovery/queue/status`);
      if (response.ok) {
        const data = await response.json();
        setQueueStats(data.queue_stats);
        setCrawlHistory(data.history);
      }
    } catch (e) {
      console.error("Error loading queue metrics:", e);
    }
  };

  const handleAddSeed = async (e: React.FormEvent) => {
    e.preventDefault();
    setSeedError("");
    setSeedSuccess("");
    if (!newSeedUrl.trim()) return;

    const token = localStorage.getItem("token");
    if (!token) {
      setSeedError("Authorization token missing. Please authenticate first.");
      return;
    }

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/discovery/queue/add`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          url: newSeedUrl,
          source_type: newSourceType,
          priority: newPriority
        })
      });

      if (response.ok) {
        setNewSeedUrl("");
        setSeedSuccess("URL registered in crawl queue!");
        fetchCrawlQueueStatus();
      } else {
        const err = await response.json();
        setSeedError(err.detail || "Failed to register seed URL.");
      }
    } catch (e) {
      setSeedError("Network connection failed.");
    }
  };

  const handleTriggerCrawl = async () => {
    setTriggerLoading(true);
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please sign in to trigger background crawling.");
      setTriggerLoading(false);
      return;
    }

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/discovery/queue/trigger`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (response.ok) {
        alert("Spiritual intelligence crawler cycle triggered in the background.");
        setTimeout(fetchCrawlQueueStatus, 1500);
      } else {
        alert("Crawler trigger rejected.");
      }
    } catch (e) {
      alert("Network error occurred.");
    }
    setTriggerLoading(false);
  };

  // Node-link physics tick simulator
  useEffect(() => {
    if (graphData.nodes.length === 0) return;
    
    // Set random start spots
    const width = 800;
    const height = 500;
    const initialNodes = graphData.nodes.map(n => ({
      ...n,
      x: width / 2 + (Math.random() - 0.5) * 180,
      y: height / 2 + (Math.random() - 0.5) * 180,
      vx: 0,
      vy: 0
    }));
    setSimulationNodes(initialNodes);
  }, [graphData]);

  useEffect(() => {
    if (simulationNodes.length === 0 || activeTab !== "graph") return;
    
    let frameId: number;
    const width = 800;
    const height = 500;
    
    const rep = 1600;
    const k = 0.07;
    const grav = 0.035;
    const friction = 0.82;
    const desired = 85;

    const tick = () => {
      setSimulationNodes(prev => {
        const nodes = prev.map(n => ({ ...n }));
        
        // Coulomb repulsion
        for (let i = 0; i < nodes.length; i++) {
          const n1 = nodes[i];
          for (let j = i + 1; j < nodes.length; j++) {
            const n2 = nodes[j];
            const dx = (n1.x || 400) - (n2.x || 400);
            const dy = (n1.y || 250) - (n2.y || 250);
            const distSq = dx * dx + dy * dy || 0.1;
            const dist = Math.sqrt(distSq);
            if (dist < 260) {
              const force = rep / (distSq + 120);
              const fx = (dx / dist) * force;
              const fy = (dy / dist) * force;
              n1.vx = (n1.vx || 0) + fx;
              n1.vy = (n1.vy || 0) + fy;
              n2.vx = (n2.vx || 0) - fx;
              n2.vy = (n2.vy || 0) - fy;
            }
          }
        }

        // Hooke attraction along links
        graphData.links.forEach(link => {
          const sId = typeof link.source === "object" ? (link.source as any).id : link.source;
          const tId = typeof link.target === "object" ? (link.target as any).id : link.target;
          const n1 = nodes.find(n => n.id === sId);
          const n2 = nodes.find(n => n.id === tId);
          if (n1 && n2) {
            const dx = (n1.x || 400) - (n2.x || 400);
            const dy = (n1.y || 250) - (n2.y || 250);
            const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
            const force = k * (dist - desired);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx = (n1.vx || 0) - fx;
            n1.vy = (n1.vy || 0) - fy;
            n2.vx = (n2.vx || 0) + fx;
            n2.vy = (n2.vy || 0) + fy;
          }
        });

        // Update positions
        nodes.forEach(n => {
          if (n.id === draggingNodeId) return;
          
          const dx = width / 2 - (n.x || 400);
          const dy = height / 2 - (n.y || 250);
          n.vx = (n.vx || 0) + dx * grav;
          n.vy = (n.vy || 0) + dy * grav;
          
          n.vx *= friction;
          n.vy *= friction;
          
          n.x = (n.x || 400) + n.vx;
          n.y = (n.y || 250) + n.vy;
          
          n.x = Math.max(25, Math.min(width - 25, n.x));
          n.y = Math.max(25, Math.min(height - 25, n.y));
        });

        return nodes;
      });
      frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [simulationNodes.length, graphData.links, draggingNodeId, activeTab]);

  const handleMouseDown = (node: GraphNodeData) => {
    setDraggingNodeId(node.id);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingNodeId || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 800;
    const y = ((e.clientY - rect.top) / rect.height) * 500;
    setSimulationNodes(prev => prev.map(n => n.id === draggingNodeId ? { ...n, x, y, vx: 0, vy: 0 } : n));
  };

  const handleMouseUp = () => {
    setDraggingNodeId(null);
  };

  const handleTouchStart = (node: GraphNodeData) => {
    setDraggingNodeId(node.id);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!draggingNodeId || !svgRef.current || e.touches.length === 0) return;
    const rect = svgRef.current.getBoundingClientRect();
    const touch = e.touches[0];
    const x = ((touch.clientX - rect.left) / rect.width) * 800;
    const y = ((touch.clientY - rect.top) / rect.height) * 500;
    setSimulationNodes(prev => prev.map(n => n.id === draggingNodeId ? { ...n, x, y, vx: 0, vy: 0 } : n));
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case "deity": return "#FF9F1C"; // gold
      case "guru":
      case "speaker": return "#E07A5F"; // amber orange
      case "scripture": return "#2EC4B6"; // cyan teal
      case "concept":
      case "tradition": return "#8338EC"; // royal purple
      case "video": return "#3B82F6"; // blue
      default: return "#6B7280";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-gradient-to-r from-card/85 to-background border border-sacred-border rounded-xl p-6 gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <Tv className="h-6 w-6 text-saffron" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Garuda SpiritualTube</h2>
            <span className="text-[10px] bg-saffron/10 border border-saffron/20 text-saffron font-bold px-2 py-0.5 rounded-full uppercase font-mono">
              Intelligence Discovery Engine
            </span>
          </div>
          <p className="text-xs text-muted-sacred max-w-2xl leading-relaxed">
            Continuously crawls, semantically indexes, and classifies Hindu spiritual lectures, mantras, and bhajans 
            across the internet. Strips all distractions, advertisements, comments, and addictive algorithmic traps.
          </p>
        </div>

        {/* Safe Mode Switch */}
        <div className="flex items-center gap-3 bg-card border border-sacred-border rounded-lg px-4 py-2 self-stretch md:self-auto justify-between">
          <div className="text-left">
            <span className="text-[10px] uppercase font-mono block text-muted-sacred">Sadhana Guard</span>
            <span className={`text-xs font-bold ${safeMode ? "text-saffron" : "text-muted-sacred"}`}>
              {safeMode ? "ACTIVE (30s Mindfulness Overlay)" : "OFF"}
            </span>
          </div>
          <button 
            suppressHydrationWarning
            onClick={() => setSafeMode(!safeMode)}
            className={`w-10 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors ${safeMode ? "bg-saffron" : "bg-card-hover"}`}
          >
            <motion.div 
              layout 
              className="bg-foreground w-4 h-4 rounded-full shadow-md"
              animate={{ x: safeMode ? 16 : 0 }}
            />
          </button>
        </div>
      </div>

      {isBackendOffline && !hasYtKey && (
        <div className="bg-saffron/5 border border-saffron/25 rounded-xl p-4.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-saffron backdrop-blur-md">
          <div className="flex items-start sm:items-center gap-3">
            <span className="text-lg leading-none mt-0.5 sm:mt-0">🪔</span>
            <div>
              <span className="font-bold block sm:inline">Offline Mode:</span> Using local fallback database. Launch your local FastAPI server and specify its tunnel address in Settings to discover and crawl online videos from YouTube.
            </div>
          </div>
          <a
            href="/settings"
            className="whitespace-nowrap bg-saffron/15 hover:bg-saffron/25 border border-saffron/20 hover:border-saffron/40 text-saffron text-[10px] font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-lg transition-all"
          >
            Settings
          </a>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Column: Core Workstations (Tabs) */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Workstation Tab Switcher */}
          <div className="flex gap-1.5 p-1 bg-card/65 border border-sacred-border rounded-lg max-w-lg">
            <button
              suppressHydrationWarning
              onClick={() => setActiveTab("feed")}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all cursor-pointer ${
                activeTab === "feed" ? "bg-saffron text-background shadow" : "text-muted-sacred hover:text-foreground"
              }`}
            >
              <Compass className="h-4 w-4" />
              Feed Discovery
            </button>
            <button
              suppressHydrationWarning
              onClick={() => { setActiveTab("graph"); fetchGraphData(); }}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all cursor-pointer ${
                activeTab === "graph" ? "bg-saffron text-background shadow" : "text-muted-sacred hover:text-foreground"
              }`}
            >
              <Network className="h-4 w-4" />
              Spiritual Graph
            </button>
            <button
              suppressHydrationWarning
              onClick={() => { setActiveTab("crawl"); fetchCrawlQueueStatus(); }}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all cursor-pointer ${
                activeTab === "crawl" ? "bg-saffron text-background shadow" : "text-muted-sacred hover:text-foreground"
              }`}
            >
              <Database className="h-4 w-4" />
              Crawl Queue ({queueStats.pending || 0})
            </button>
          </div>

          {/* Search bar & Advanced Filters */}
          <div className="bg-card border border-sacred-border rounded-xl p-4.5 space-y-3">
            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-3 h-4.5 w-4.5 text-muted-sacred" />
                <input 
                  suppressHydrationWarning
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask the engine: e.g. 'Deep Advaita Vedanta lectures', 'calming Krishna bhajans'..."
                  className="w-full bg-background border border-sacred-border rounded-lg pl-10 pr-4 py-2.5 text-xs text-foreground focus:outline-none focus:border-saffron/40 transition-colors placeholder:text-muted-sacred/70 font-medium"
                />
              </div>
              <button 
                suppressHydrationWarning
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className={`border border-sacred-border px-3.5 rounded-lg flex items-center justify-center cursor-pointer transition-colors ${showFilters ? "bg-saffron/10 border-saffron/40 text-saffron" : "bg-background text-muted-sacred hover:text-foreground"}`}
                title="Search Filter Overlays"
              >
                <Sliders className="h-4 w-4" />
              </button>
              <button 
                suppressHydrationWarning
                type="submit"
                className="bg-saffron hover:bg-saffron-dim text-background font-bold text-xs px-6 py-2.5 rounded-lg transition-colors cursor-pointer"
              >
                Search
              </button>
            </form>

            {/* Collapsible Advanced Filters Drawer */}
            <AnimatePresence>
              {showFilters && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden border-t border-sacred-border/60 pt-3.5 mt-2 space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Tradition dropdown */}
                    <div className="space-y-1.5">
                      <label className="text-[10px] uppercase font-bold tracking-wider text-muted-sacred">Tradition</label>
                      <select 
                        value={tradition}
                        onChange={(e) => { setTradition(e.target.value); triggerSearch(searchQuery, e.target.value); }}
                        className="w-full bg-background border border-sacred-border text-xs rounded-lg px-3 py-2 text-foreground focus:outline-none focus:border-saffron/30 font-medium"
                      >
                        <option value="All">All Traditions</option>
                        <option value="Vaishnavism">Vaishnavism</option>
                        <option value="Shaivism">Shaivism</option>
                        <option value="Shaktism">Shaktism</option>
                        <option value="Smarta">Smarta</option>
                        <option value="Advaita">Advaita Vedanta</option>
                        <option value="Dvaita">Dvaita Vedanta</option>
                        <option value="ISKCON">ISKCON</option>
                        <option value="Yoga">Yoga Sutras</option>
                      </select>
                    </div>

                    {/* Content Category dropdown */}
                    <div className="space-y-1.5">
                      <label className="text-[10px] uppercase font-bold tracking-wider text-muted-sacred">Content Genre</label>
                      <select 
                        value={contentType}
                        onChange={(e) => { setContentType(e.target.value); triggerSearch(searchQuery, undefined, e.target.value); }}
                        className="w-full bg-background border border-sacred-border text-xs rounded-lg px-3 py-2 text-foreground focus:outline-none focus:border-saffron/30 font-medium"
                      >
                        <option value="All">All Genres</option>
                        <option value="lecture">Lecture / Discourses</option>
                        <option value="kirtan">Kirtan</option>
                        <option value="bhajan">Bhajan</option>
                        <option value="mantra">Mantra Chanting</option>
                        <option value="meditation">Guided Meditation</option>
                        <option value="storytelling">Scripture Stories</option>
                        <option value="ritual">Temple Rituals</option>
                        <option value="satsang">Satsang Meetings</option>
                        <option value="philosophy">Philosophy discussions</option>
                        <option value="podcast">Podcasts</option>
                      </select>
                    </div>

                    {/* Energy Profile dropdown */}
                    <div className="space-y-1.5">
                      <label className="text-[10px] uppercase font-bold tracking-wider text-muted-sacred">Energy Profile</label>
                      <select 
                        value={energyType}
                        onChange={(e) => { setEnergyType(e.target.value); triggerSearch(searchQuery, undefined, undefined, e.target.value); }}
                        className="w-full bg-background border border-sacred-border text-xs rounded-lg px-3 py-2 text-foreground focus:outline-none focus:border-saffron/30 font-medium"
                      >
                        <option value="All">All Profiles</option>
                        <option value="calming">Calming / Restorative</option>
                        <option value="devotional">Bhakti / Devotional</option>
                        <option value="energetic">Energetic / Uplifting</option>
                        <option value="meditative">Silent / Meditative</option>
                        <option value="intellectual">Analytical / Intellectual</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-1 bg-background/30 p-3 rounded-lg border border-sacred-border/40">
                    {/* Authenticity threshold slider */}
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between text-[10px] font-bold text-muted-sacred uppercase tracking-wider">
                        <span>Min Authenticity Audit Score</span>
                        <span className="text-saffron font-mono">{minAuthenticity}%</span>
                      </div>
                      <input 
                        type="range"
                        min={0}
                        max={100}
                        step={5}
                        value={minAuthenticity}
                        onChange={(e) => { setMinAuthenticity(parseInt(e.target.value)); triggerSearch(searchQuery, undefined, undefined, undefined, parseInt(e.target.value)); }}
                        className="w-full h-1 bg-background border border-sacred-border rounded-lg appearance-none cursor-pointer accent-saffron"
                      />
                    </div>

                    {/* Multilingual toggle */}
                    <label className="flex items-center gap-2.5 cursor-pointer select-none self-start md:self-auto">
                      <input 
                        type="checkbox"
                        checked={expandMultilingual}
                        onChange={(e) => { setExpandMultilingual(e.target.checked); triggerSearch(searchQuery, undefined, undefined, undefined, undefined, e.target.checked); }}
                        className="rounded border-sacred-border text-saffron focus:ring-0 focus:ring-offset-0 bg-background h-4 w-4 accent-saffron cursor-pointer"
                      />
                      <div className="text-left">
                        <span className="text-xs font-semibold text-foreground flex items-center gap-1">
                          <Globe className="h-3.5 w-3.5 text-saffron" /> Multilingual Query Expansion
                        </span>
                        <span className="text-[9px] text-muted-sacred block">Translates and indexes queries across Sanskrit & 9 regional languages</span>
                      </div>
                    </label>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Render Active Tab Workstation */}
          <div className="min-h-[50vh]">
            
            {/* Tab 1: Video Discovery Feed */}
            {activeTab === "feed" && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-muted-sacred flex items-center gap-1.5">
                    <Activity className="h-4 w-4 text-saffron animate-pulse" />
                    <span>Sattvic Media Discoveries</span>
                  </h3>
                  {videos.length > 0 && (
                    <span className="text-[10px] font-mono text-muted-sacred">Found {videos.length} high-authenticity matches</span>
                  )}
                </div>
                
                {loading ? (
                  <div className="flex h-64 items-center justify-center border border-dashed border-sacred-border rounded-xl bg-card/20">
                    <div className="text-center space-y-2">
                      <RefreshCw className="h-6 w-6 text-saffron animate-spin mx-auto" />
                      <span className="text-xs text-muted-sacred font-medium block animate-pulse">Running advanced hybrid discovery search...</span>
                    </div>
                  </div>
                ) : videos.length === 0 && hasSearched && isBackendOffline ? (
                  <div className="flex h-64 items-center justify-center border border-dashed border-sacred-border rounded-xl bg-card/25 text-center p-6">
                    <div className="max-w-md space-y-4 animate-fade-in">
                      <div className="text-3xl">🪔</div>
                      <h4 className="text-sm font-semibold text-foreground">No Offline Matches Found</h4>
                      <p className="text-xs text-muted-sacred leading-relaxed">
                        We couldn't find any offline videos matching <strong className="text-saffron">&ldquo;{lastQuery}&rdquo;</strong>.
                        Please launch your local FastAPI server and configure it in Settings to search the live web.
                      </p>
                      <button 
                        onClick={() => { setSearchQuery(""); fetchCuratedVideos(); }}
                        className="text-xs font-bold bg-saffron/10 border border-saffron/20 hover:bg-saffron text-saffron hover:text-background px-4 py-2 rounded-lg transition-colors cursor-pointer"
                      >
                        Clear Search & Show All Offline Videos
                      </button>
                    </div>
                  </div>
                ) : videos.length === 0 && hasSearched ? (
                  <div className="flex h-64 items-center justify-center border border-dashed border-sacred-border rounded-xl bg-card/25 text-center p-6">
                    <div className="max-w-sm space-y-3">
                      <div className="text-3xl">🕉️</div>
                      <h4 className="text-sm font-semibold text-foreground">Only Hindu Spiritual Content</h4>
                      <p className="text-xs text-muted-sacred leading-relaxed">
                        <strong className="text-saffron">&ldquo;{lastQuery}&rdquo;</strong> does not appear to be a spiritual topic.
                        This is a sacred Hindu media engine — please search for mantras, bhajans, scriptures, deities, gurus, or spiritual practices.
                      </p>
                      <p className="text-[10px] text-muted-sacred/70">Try: <span className="text-saffron/80">Bhagavad Gita · Hanuman Chalisa · Shiva mantra · Krishna bhajan · Vedanta lecture</span></p>
                    </div>
                  </div>
                ) : videos.length === 0 ? (
                  <div className="flex h-64 items-center justify-center border border-dashed border-sacred-border rounded-xl bg-card/25 text-center p-6">
                    <div className="max-w-sm space-y-2">
                      <div className="text-3xl">🪔</div>
                      <h4 className="text-sm font-semibold text-foreground">Search for Hindu Spiritual Content</h4>
                      <p className="text-xs text-muted-sacred leading-relaxed">
                        Enter a mantra, bhajan, deity, scripture, guru name, or spiritual practice to discover videos.
                      </p>
                      <p className="text-[10px] text-muted-sacred/70">e.g. <span className="text-saffron/80">Bhagavad Gita · Shiva Tandava · Devi Mahatmyam · Sadhguru</span></p>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {videos.map((vid) => (
                      <div 
                        key={vid.youtube_id} 
                        onClick={() => selectVideo(vid)}
                        className="group bg-card border border-sacred-border rounded-xl overflow-hidden hover:border-saffron/30 transition-all duration-300 cursor-pointer flex flex-col justify-between"
                      >
                        <div className="aspect-video bg-background relative overflow-hidden">
                          <img 
                            src={vid.thumbnail_url || `https://img.youtube.com/vi/${vid.youtube_id}/0.jpg`} 
                            alt={vid.title}
                            className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity duration-300">
                            <div className="h-10 w-10 bg-saffron text-background rounded-full flex items-center justify-center font-bold">
                              <Play className="h-4.5 w-4.5 fill-current" />
                            </div>
                          </div>
                          <span className="absolute bottom-2 right-2 bg-background/80 border border-sacred-border/60 text-[9px] px-1.5 py-0.5 rounded font-mono text-muted-sacred">
                            {formatTime(vid.duration)}
                          </span>
                          {vid.authenticity_score !== undefined && (
                            <span className="absolute top-2 left-2 bg-saffron text-background border border-saffron/20 text-[9px] font-bold px-1.5 py-0.5 rounded shadow-md">
                              ★ Audit: {vid.authenticity_score}
                            </span>
                          )}
                        </div>
                        <div className="p-4 space-y-1.5 flex-1 flex flex-col justify-between">
                          <div className="space-y-1">
                            <div className="flex justify-between items-center text-[9px] font-bold text-saffron uppercase tracking-wider">
                              <span>{vid.category}</span>
                              {vid.spiritual_tradition && <span className="text-[8px] bg-saffron/10 border border-saffron/20 px-1 rounded">{vid.spiritual_tradition}</span>}
                            </div>
                            <h4 className="text-xs font-bold text-foreground leading-snug line-clamp-2 group-hover:text-saffron transition-colors">
                              {vid.title}
                            </h4>
                            <p className="text-[11px] text-muted-sacred line-clamp-2 leading-relaxed">
                              {vid.description}
                            </p>
                          </div>
                          
                          {/* Metadata row */}
                          <div className="pt-2 border-t border-sacred-border/50 flex flex-wrap gap-1.5 items-center justify-between text-[9px] text-muted-sacred font-medium mt-3">
                            <span>By: {vid.speaker_name || "Guru"}</span>
                            {vid.energy_type && <span className="bg-background border border-sacred-border/80 px-1 py-0.2 rounded text-[8px] uppercase">{vid.energy_type}</span>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Spiritual Relationship Graph */}
            {activeTab === "graph" && (
              <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-4">
                <div className="flex flex-col md:flex-row justify-between md:items-center gap-2 border-b border-sacred-border/60 pb-3">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-saffron">Spiritual media network graph</h3>
                    <p className="text-[10px] text-muted-sacred">
                      Drag nodes to explore. Click on a Deity, Guru, or Scripture node to discover related video content feeds.
                    </p>
                  </div>
                  <button
                    onClick={fetchGraphData}
                    className="self-start md:self-auto text-[9px] uppercase tracking-wider font-semibold border border-sacred-border hover:bg-card-hover text-muted-sacred px-2 py-1 rounded flex items-center gap-1"
                  >
                    <RefreshCw className="h-3 w-3" /> Refresh Graph
                  </button>
                </div>

                {/* Graph View Box */}
                <div className="relative border border-sacred-border rounded-xl bg-[#090a0c] overflow-hidden select-none">
                  {graphData.nodes.length === 0 ? (
                    <div className="h-96 flex items-center justify-center text-xs text-muted-sacred animate-pulse">
                      Graph index loading...
                    </div>
                  ) : (
                    <svg
                      ref={svgRef}
                      viewBox="0 0 800 500"
                      className="w-full h-auto max-h-[60vh] cursor-grab active:cursor-grabbing"
                      onMouseMove={handleMouseMove}
                      onMouseUp={handleMouseUp}
                      onMouseLeave={handleMouseUp}
                    >
                      {/* Relationship Lines */}
                      {simulationNodes.length > 0 && graphData.links.map((link, idx) => {
                        const sId = typeof link.source === "object" ? (link.source as any).id : link.source;
                        const tId = typeof link.target === "object" ? (link.target as any).id : link.target;
                        const src = simulationNodes.find(n => n.id === sId);
                        const tgt = simulationNodes.find(n => n.id === tId);
                        if (!src || !tgt) return null;
                        return (
                          <line
                            key={idx}
                            x1={src.x}
                            y1={src.y}
                            x2={tgt.x}
                            y2={tgt.y}
                            stroke="rgba(241, 168, 10, 0.15)"
                            strokeWidth={1 + link.weight * 0.45}
                          />
                        );
                      })}

                      {/* Interaction Node circles */}
                      {simulationNodes.map(node => (
                        <g
                          key={node.id}
                          transform={`translate(${node.x || 400}, ${node.y || 250})`}
                          className="group cursor-pointer"
                          onMouseDown={() => handleMouseDown(node)}
                          onTouchStart={() => handleTouchStart(node)}
                          onTouchMove={handleTouchMove}
                          onTouchEnd={handleMouseUp}
                          onMouseEnter={() => setHoveredNode(node)}
                          onMouseLeave={() => setHoveredNode(null)}
                          onClick={() => {
                            setSearchQuery(node.name);
                            setActiveTab("feed");
                            triggerSearch(node.name);
                          }}
                        >
                          <circle
                            r={node.type === "video" ? 6 : 9}
                            fill={getNodeColor(node.type)}
                            stroke="#0b0c10"
                            strokeWidth={1.5}
                            className="transition-transform group-hover:scale-125 duration-100"
                          />
                          <text
                            y={17}
                            textAnchor="middle"
                            fill="#F3F4F6"
                            fontSize="9px"
                            fontWeight="600"
                            className="pointer-events-none drop-shadow-[0_1.5px_2.5px_rgba(0,0,0,0.95)]"
                          >
                            {node.name.length > 18 ? `${node.name.slice(0, 16)}..` : node.name}
                          </text>
                        </g>
                      ))}
                    </svg>
                  )}

                  {/* Graph Overlay Tooltip detail */}
                  {hoveredNode && (
                    <div className="absolute bottom-4 left-4 right-4 md:right-auto md:w-80 bg-black/90 border border-sacred-border p-3.5 rounded-lg shadow-xl text-xs space-y-1 animate-fade-in pointer-events-none backdrop-blur-md">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-foreground text-sm">{hoveredNode.name}</span>
                        <span className="text-[8px] uppercase tracking-widest font-mono font-bold px-1.5 py-0.5 rounded bg-saffron/10 border border-saffron/20 text-saffron">
                          {hoveredNode.type}
                        </span>
                      </div>
                      {hoveredNode.description && (
                        <p className="text-muted-sacred text-[11px] leading-relaxed pt-1.5">
                          {hoveredNode.description}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Graph Legend */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-2 text-[10px] text-muted-sacred font-semibold bg-background/50 p-3 rounded-lg border border-sacred-border/60">
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#FF9F1C" }}></span> Deity</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#E07A5F" }}></span> Guru / Speaker</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#2EC4B6" }}></span> Sacred Scripture</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#8338EC" }}></span> Concept / Tradition</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#3B82F6" }}></span> Media Node</div>
                </div>
              </div>
            )}

            {/* Tab 3: Continuous Crawl Queue Monitor */}
            {activeTab === "crawl" && (
              <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-6">
                
                {/* Upper Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                    <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Crawler status</span>
                    <span className="text-sm font-bold text-emerald-500 mt-1 block uppercase font-mono animate-pulse">Running</span>
                  </div>
                  <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                    <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Pending queue</span>
                    <span className="text-lg font-bold text-saffron mt-1 block font-mono">{queueStats.pending || 0}</span>
                  </div>
                  <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                    <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">In-flight active</span>
                    <span className="text-lg font-bold text-amber-500 mt-1 block font-mono">{queueStats.processing || 0}</span>
                  </div>
                  <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                    <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Completed seeds</span>
                    <span className="text-lg font-bold text-emerald-600 mt-1 block font-mono">{queueStats.completed || 0}</span>
                  </div>
                  <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                    <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Failed runs</span>
                    <span className="text-lg font-bold text-red-500 mt-1 block font-mono">{queueStats.failed || 0}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
                  
                  {/* Left block: Add Seed URL Form */}
                  <div className="md:col-span-1 bg-background/50 border border-sacred-border p-4 rounded-xl space-y-4">
                    <div className="border-b border-sacred-border/60 pb-2 flex justify-between items-center">
                      <span className="text-xs font-bold uppercase tracking-wider text-saffron flex items-center gap-1.5">
                        <Plus className="h-4 w-4" /> Add Discovery Seed
                      </span>
                    </div>

                    <form onSubmit={handleAddSeed} className="space-y-3.5">
                      <div className="space-y-1.5">
                        <label className="text-[10px] uppercase font-bold text-muted-sacred">Crawl target URL</label>
                        <input 
                          type="text"
                          value={newSeedUrl}
                          onChange={(e) => setNewSeedUrl(e.target.value)}
                          placeholder="e.g. YouTube channel/playlist or Podcast RSS"
                          className="w-full bg-card border border-sacred-border text-xs rounded-lg px-3 py-2 text-foreground focus:outline-none focus:border-saffron/30"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[10px] uppercase font-bold text-muted-sacred">Source Type</label>
                        <select 
                          value={newSourceType}
                          onChange={(e) => setNewSourceType(e.target.value)}
                          className="w-full bg-card border border-sacred-border text-xs rounded-lg px-3 py-2 text-foreground focus:outline-none focus:border-saffron/30"
                        >
                          <option value="youtube_channel">YouTube Channel</option>
                          <option value="youtube_playlist">YouTube Playlist</option>
                          <option value="archive_org">Archive.org Search</option>
                          <option value="podcast_feed">Podcast RSS Feed</option>
                          <option value="sitemap">Website XML Sitemap</option>
                          <option value="rss_feed">Generic RSS News feed</option>
                        </select>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[10px] uppercase font-bold text-muted-sacred">Crawl Priority (0 - 10)</label>
                        <input 
                          type="number"
                          min={0}
                          max={10}
                          value={newPriority}
                          onChange={(e) => setNewPriority(parseInt(e.target.value) || 0)}
                          className="w-full bg-card border border-sacred-border text-xs rounded-lg px-3 py-2 text-foreground focus:outline-none focus:border-saffron/30 font-mono"
                        />
                      </div>

                      {seedError && <p className="text-[10px] font-bold text-red-400">{seedError}</p>}
                      {seedSuccess && <p className="text-[10px] font-bold text-emerald-400">{seedSuccess}</p>}

                      <button
                        type="submit"
                        className="w-full bg-saffron hover:bg-saffron-dim text-background text-xs font-bold py-2 rounded-lg transition-colors cursor-pointer"
                      >
                        Queue Discovery Target
                      </button>
                    </form>

                    <div className="pt-2 border-t border-sacred-border/60">
                      <button
                        onClick={handleTriggerCrawl}
                        disabled={triggerLoading}
                        className="w-full bg-card-hover border border-sacred-border text-muted-sacred hover:text-foreground text-xs font-semibold py-2 rounded-lg transition-colors cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${triggerLoading ? "animate-spin" : ""}`} />
                        {triggerLoading ? "Activating Crawler..." : "Trigger Discovery Cycle Now"}
                      </button>
                    </div>
                  </div>

                  {/* Right block: Discovery Crawl logs */}
                  <div className="md:col-span-2 bg-background/50 border border-sacred-border p-4 rounded-xl flex flex-col">
                    <div className="border-b border-sacred-border/60 pb-2 mb-3.5 flex justify-between items-center">
                      <span className="text-xs font-bold uppercase tracking-wider text-saffron flex items-center gap-1.5">
                        <Activity className="h-4 w-4" /> Discovery Execution Logs
                      </span>
                    </div>

                    <div className="flex-1 overflow-x-auto">
                      <table className="w-full text-[11px] text-left">
                        <thead>
                          <tr className="border-b border-sacred-border text-muted-sacred font-bold text-[9px] uppercase tracking-wider">
                            <th className="py-2 pr-2">Target URL</th>
                            <th className="py-2 px-2">Type</th>
                            <th className="py-2 px-2">Status</th>
                            <th className="py-2 px-2 text-right">Discovered</th>
                            <th className="py-2 pl-2 text-right">Duration</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-sacred-border/30">
                          {crawlHistory.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-muted-sacred italic">No discovery cycles completed yet.</td>
                            </tr>
                          ) : (
                            crawlHistory.map((h, index) => (
                              <tr key={index} className="hover:bg-card/25 transition-colors">
                                <td className="py-2.5 pr-2 max-w-[160px] truncate font-mono text-[10px] text-foreground" title={h.url}>
                                  {h.url}
                                </td>
                                <td className="py-2.5 px-2 text-muted-sacred font-mono text-[9px] uppercase">{h.source_type}</td>
                                <td className="py-2.5 px-2">
                                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wide ${
                                    h.status === "completed" ? "bg-emerald-950 text-emerald-400 border border-emerald-500/20" : "bg-red-950 text-red-400 border border-red-500/20"
                                  }`}>
                                    {h.status}
                                  </span>
                                </td>
                                <td className="py-2.5 px-2 text-right font-mono font-bold text-foreground">{h.discovered_count} items</td>
                                <td className="py-2.5 pl-2 text-right font-mono text-muted-sacred">{h.duration_seconds}s</td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                </div>
              </div>
            )}

          </div>
        </div>

        {/* Right Column: Curated Learning Paths & Info */}
        <div className="space-y-6">
          <div className="bg-card border border-sacred-border rounded-xl p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-sacred flex items-center gap-2 mb-4">
              <Compass className="h-4 w-4 text-saffron" />
              <span>Curated Learning Paths</span>
            </h3>

            <div className="space-y-4">
              {paths.map((p) => (
                <div key={p.id} className="border-b border-sacred-border/50 pb-3 last:border-b-0 last:pb-0 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] bg-saffron/10 border border-saffron/15 text-saffron px-2 py-0.5 rounded font-bold">
                      {p.level}
                    </span>
                    <span className="text-[9px] text-muted-sacred font-mono font-medium">{p.category}</span>
                  </div>
                  <h4 className="text-xs font-bold text-foreground hover:text-saffron transition-colors cursor-pointer">
                    {p.name}
                  </h4>
                  <p className="text-[11px] text-muted-sacred leading-relaxed">{p.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-card/40 border border-sacred-border border-dashed rounded-xl p-5 text-center">
            <ShieldCheck className="h-7 w-7 text-saffron mx-auto mb-2.5 animate-pulse" />
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wide">Continuous Audit Active</h4>
            <p className="text-[10px] text-muted-sacred mt-1 leading-relaxed">
              Every video indexed undergoes automatic translation, LLM auditing, scripture verification, and energy profiling.
            </p>
          </div>
        </div>

      </div>

      {/* Floating Video Player Modal */}
      <AnimatePresence>
        {activeVideo && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-6 backdrop-blur-sm"
          >
            <motion.div 
              initial={{ scale: 0.95, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 15 }}
              className="bg-card border border-sacred-border rounded-xl w-full max-w-6xl h-[80vh] flex flex-col md:flex-row overflow-hidden shadow-2xl"
            >
              {/* Left Side: Video Player */}
              <div className="flex-1 bg-black relative flex flex-col justify-between">
                {/* Safe Mode warning overlay */}
                {showMindfulWarning && (
                  <div className="absolute inset-x-0 top-0 z-10 bg-amber-950/90 border-b border-saffron/20 p-3 text-center text-xs text-saffron flex items-center justify-center gap-2">
                    <span className="font-bold">Mindful Notice:</span> You have been watching for 30 seconds. Contemplate the teaching. Take a breath.
                    <button 
                      onClick={() => setShowMindfulWarning(false)}
                      className="ml-4 px-2 py-0.5 bg-saffron text-background rounded font-bold text-[10px] cursor-pointer"
                    >
                      Acknowledge
                    </button>
                  </div>
                )}

                <div className="flex-1 w-full relative">
                  <iframe 
                    src={`https://www.youtube.com/embed/${activeVideo.youtube_id}?autoplay=1&rel=0&showinfo=0`}
                    title={activeVideo.title}
                    allow="autoplay; encrypted-media"
                    allowFullScreen
                    className="w-full h-full border-0"
                  />
                </div>

                <div className="bg-card p-4 border-t border-sacred-border">
                  <span className="text-[10px] text-saffron font-bold uppercase tracking-wider">{activeVideo.category}</span>
                  <h3 className="text-sm font-bold text-foreground mt-0.5">{activeVideo.title}</h3>
                  <div className="flex gap-4 mt-2 text-[11px] text-muted-sacred">
                    <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Played: {formatTime(playbackSeconds)}</span>
                    <span>Safe mode: {safeMode ? "Enabled" : "Disabled"}</span>
                  </div>
                </div>
              </div>

              {/* Right Side: Notes and AI Insights Panel */}
              <div className="w-full md:w-96 border-l border-sacred-border flex flex-col bg-card h-full">
                {/* Tabs / Header */}
                <div className="border-b border-sacred-border p-3 flex justify-between items-center bg-card-hover">
                  <span className="text-xs font-bold uppercase tracking-wider text-foreground">Sadhana Study Workspace</span>
                  <button 
                    onClick={closeVideo}
                    className="text-xs text-muted-sacred hover:text-foreground cursor-pointer font-bold"
                  >
                    Close [X]
                  </button>
                </div>

                {/* Pane Content */}
                <div className="flex-1 overflow-y-auto p-4 space-y-5">
                  {/* AI Summary Section */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-saffron uppercase flex items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5" /> AI Reflection Summary
                      </span>
                      {!activeVideo.summary || activeVideo.summary.includes("No AI summary") ? (
                        <button 
                          onClick={generateAISummary}
                          disabled={aiSummaryLoading}
                          className="text-[10px] bg-saffron/10 border border-saffron/20 hover:bg-saffron text-saffron hover:text-background px-2 py-0.5 rounded font-bold cursor-pointer disabled:opacity-50"
                        >
                          {aiSummaryLoading ? "Summarizing..." : "Generate Insights"}
                        </button>
                      ) : null}
                    </div>

                    {activeVideo.summary && (
                      <p className="text-xs text-muted-sacred leading-relaxed bg-background/55 p-3 rounded-lg border border-sacred-border">
                        {activeVideo.summary}
                      </p>
                    )}

                    {aiTeachings && (
                      <div className="space-y-2.5 bg-saffron/5 border border-saffron/10 p-3 rounded-lg text-xs">
                        <div>
                          <span className="font-bold text-saffron block mb-1">Core Teachings:</span>
                          <ul className="list-disc pl-4 space-y-1 text-muted-sacred text-[11px]">
                            {aiTeachings.teachings?.map((t: string, idx: number) => (
                              <li key={idx}>{t}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <span className="font-bold text-saffron block mb-1">Reflection Prompts:</span>
                          <ul className="list-disc pl-4 space-y-1 text-muted-sacred text-[11px]">
                            {aiTeachings.reflection_questions?.map((q: string, idx: number) => (
                              <li key={idx}>{q}</li>
                            ))}
                          </ul>
                        </div>
                        {aiTeachings.sadhana_practice && (
                          <div>
                            <span className="font-bold text-saffron block mb-0.5">Sadhana Practice:</span>
                            <p className="text-[11px] text-muted-sacred leading-relaxed">{aiTeachings.sadhana_practice}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Devotee Notes Section */}
                  <div className="space-y-3 pt-3 border-t border-sacred-border/60">
                    <span className="text-xs font-bold text-saffron uppercase flex items-center gap-1.5">
                      <MessageSquare className="h-3.5 w-3.5" /> Study Notes
                    </span>

                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {videoNotes.length === 0 ? (
                        <p className="text-[10px] text-muted-sacred italic text-center py-2">No study notes taken yet.</p>
                      ) : (
                        videoNotes.map((note) => (
                          <div key={note.id} className="bg-background/40 border border-sacred-border rounded-lg p-2 flex justify-between items-start gap-2">
                            <div className="space-y-1">
                              <span className="text-[9px] bg-card border border-sacred-border text-saffron px-1 rounded font-mono font-bold">
                                {formatTime(note.timestamp)}
                              </span>
                              <p className="text-xs text-foreground leading-relaxed">{note.note_text}</p>
                            </div>
                            <button 
                              onClick={() => deleteNote(note.id)}
                              className="text-muted-sacred hover:text-overloaded transition-colors cursor-pointer"
                            >
                              <Trash className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Add note inputs */}
                    <div className="space-y-2 bg-background/50 border border-sacred-border p-2.5 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-muted-sacred font-bold">Note at:</span>
                        <input 
                          type="number"
                          value={noteTimestamp}
                          onChange={(e) => setNoteTimestamp(Math.max(0, parseInt(e.target.value) || 0))}
                          className="w-16 bg-card border border-sacred-border text-xs rounded text-center px-1 text-saffron font-mono focus:outline-none"
                        />
                        <button 
                          onClick={() => setNoteTimestamp(playbackSeconds)}
                          className="text-[9px] bg-card hover:bg-card-hover border border-sacred-border px-1.5 py-0.5 rounded text-muted-sacred font-semibold cursor-pointer"
                        >
                          Use Current
                        </button>
                      </div>
                      <div className="flex gap-1.5">
                        <input 
                          type="text"
                          value={noteText}
                          onChange={(e) => setNoteText(e.target.value)}
                          placeholder="Type realization..."
                          className="flex-1 bg-card border border-sacred-border text-xs rounded px-2 py-1 focus:outline-none"
                        />
                        <button 
                          onClick={addNote}
                          className="bg-saffron text-background p-1 rounded hover:bg-saffron-dim cursor-pointer"
                        >
                          <Plus className="h-4.5 w-4.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
