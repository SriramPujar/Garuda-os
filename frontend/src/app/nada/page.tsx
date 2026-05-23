"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getApiUrl } from "@/utils/api";
import { 
  Play, 
  Pause, 
  Volume2, 
  RotateCcw, 
  Music, 
  BookOpen, 
  Infinity as InfinityIcon,
  Search,
  Sparkles,
  Heart,
  VolumeX,
  Sliders,
  Globe,
  Activity,
  Network,
  Database,
  RefreshCw,
  Plus,
  Trash,
  ExternalLink
} from "lucide-react";

interface Track {
  id: number;
  title: string;
  artist: string;
  url: string;
  category: string;
  deity?: string;
  lyrics?: string;
  meaning?: string;
  mood_tags?: string;
  spiritual_intensity: number;
  is_mantra_loopable: boolean;
  duration: number;
  authenticity_score?: number;
  spiritual_tradition?: string;
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

export default function GarudaNada() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [activeTrack, setActiveTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const isSpotifyTrack = (url: string) => url.includes("spotify.com") || url.startsWith("spotify:");
  const isYoutubeTrack = (url: string) => url.includes("youtube.com") || url.includes("youtu.be");

  const getSpotifyId = (url: string) => {
    if (url.startsWith("spotify:track:")) {
      return url.split(":")[2];
    }
    const match = url.match(/\/track\/([a-zA-Z0-9]+)/);
    return match ? match[1] : "";
  };

  const getYoutubeId = (url: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : "";
  };
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("All");

  // Playback state
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Mantra loop engine
  const [loopCountSetting, setLoopCountSetting] = useState<number | "infinite">(108);
  const [completedLoops, setCompletedLoops] = useState(0);

  // Ambient sound mixers (volume from 0 to 1)
  const [ambientBells, setAmbientBells] = useState(0);
  const [ambientRain, setAmbientRain] = useState(0);
  const [ambientConch, setAmbientConch] = useState(0);
  const [ambientForest, setAmbientForest] = useState(0);

  // Lyrics translations
  const [lyricsTranslation, setLyricsTranslation] = useState<string | null>(null);
  const [translating, setTranslating] = useState(false);

  // Tabs state
  const [activeTab, setActiveTab] = useState<"tracks" | "graph" | "crawl">("tracks");

  // Advanced Filters State
  const [showFilters, setShowFilters] = useState(false);
  const [tradition, setTradition] = useState("All");
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
  const [newSourceType, setNewSourceType] = useState("podcast_feed");
  const [newPriority, setNewPriority] = useState(0);
  const [seedError, setSeedError] = useState("");
  const [seedSuccess, setSeedSuccess] = useState("");
  const [triggerLoading, setTriggerLoading] = useState(false);

  // HTML5 audio elements refs
  const mainAudioRef = useRef<HTMLAudioElement | null>(null);
  const bellsAudioRef = useRef<HTMLAudioElement | null>(null);
  const rainAudioRef = useRef<HTMLAudioElement | null>(null);
  const conchAudioRef = useRef<HTMLAudioElement | null>(null);
  const forestAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchTracks();
    
    // Initialize ambient audios
    bellsAudioRef.current = new Audio("/sounds/bell.ogg?v=1");
    rainAudioRef.current = new Audio("/sounds/rain.ogg?v=1");
    conchAudioRef.current = new Audio("/sounds/conch.ogg?v=1");
    forestAudioRef.current = new Audio("/sounds/birds.ogg?v=1");

    // Configure loops
    bellsAudioRef.current.loop = true;
    rainAudioRef.current.loop = true;
    conchAudioRef.current.loop = true;
    forestAudioRef.current.loop = true;

    return () => {
      mainAudioRef.current?.pause();
      bellsAudioRef.current?.pause();
      rainAudioRef.current?.pause();
      conchAudioRef.current?.pause();
      forestAudioRef.current?.pause();
    };
  }, []);

  useEffect(() => {
    if (bellsAudioRef.current) bellsAudioRef.current.volume = ambientBells;
    if (ambientBells > 0 && isPlaying) {
      bellsAudioRef.current?.play().catch(() => {});
    } else {
      bellsAudioRef.current?.pause();
    }
  }, [ambientBells, isPlaying]);

  useEffect(() => {
    if (rainAudioRef.current) rainAudioRef.current.volume = ambientRain;
    if (ambientRain > 0 && isPlaying) {
      rainAudioRef.current?.play().catch(() => {});
    } else {
      rainAudioRef.current?.pause();
    }
  }, [ambientRain, isPlaying]);

  useEffect(() => {
    if (conchAudioRef.current) conchAudioRef.current.volume = ambientConch;
    if (ambientConch > 0 && isPlaying) {
      conchAudioRef.current?.play().catch(() => {});
    } else {
      conchAudioRef.current?.pause();
    }
  }, [ambientConch, isPlaying]);

  useEffect(() => {
    if (forestAudioRef.current) forestAudioRef.current.volume = ambientForest;
    if (ambientForest > 0 && isPlaying) {
      forestAudioRef.current?.play().catch(() => {});
    } else {
      forestAudioRef.current?.pause();
    }
  }, [ambientForest, isPlaying]);

  const fetchTracks = async (catName?: string) => {
    setLoading(true);
    const selected = catName || category;

    if (searchQuery.trim() || tradition !== "All" || minAuthenticity > 0) {
      await triggerSearch(searchQuery, tradition, selected);
      setLoading(false);
      return;
    }

    let url = `${getApiUrl()}/api/v1/nada/tracks`;
    if (selected !== "All") {
      url += `?category=${selected}`;
    }
    try {
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setTracks(data);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  // Hybrid Search logic using advanced discovery router
  const triggerSearch = async (queryText: string, currentTradition?: string, currentCategory?: string, currentMinAuth?: number, currentExpand?: boolean) => {
    setLoading(true);
    try {
      const trad = currentTradition !== undefined ? currentTradition : tradition;
      const cat = currentCategory !== undefined ? currentCategory : category;
      const minAuth = currentMinAuth !== undefined ? currentMinAuth : minAuthenticity;
      const exp = currentExpand !== undefined ? currentExpand : expandMultilingual;

      let url = `${getApiUrl()}/api/v1/discovery/search/audio?query=${encodeURIComponent(queryText)}`;
      if (trad && trad !== "All") url += `&tradition=${encodeURIComponent(trad)}`;
      if (cat && cat !== "All") url += `&category=${encodeURIComponent(cat)}`;
      if (minAuth > 0) url += `&min_authenticity=${minAuth}`;
      url += `&expand=${exp}`;

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setTracks(data);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    triggerSearch(searchQuery);
  };

  const selectTrack = (track: Track) => {
    if (mainAudioRef.current) {
      mainAudioRef.current.pause();
      mainAudioRef.current = null;
    }
    
    setActiveTrack(track);
    setLyricsTranslation(null);
    setCompletedLoops(0);
    
    const isDirect = !track.url.includes("spotify.com") && !track.url.includes("youtube.com") && !track.url.includes("youtu.be") && !track.url.startsWith("spotify:");
    
    if (isDirect) {
      const audio = new Audio(track.url);
      mainAudioRef.current = audio;
      
      audio.addEventListener("timeupdate", () => {
        setCurrentTime(audio.currentTime);
      });

      audio.addEventListener("loadedmetadata", () => {
        setDuration(audio.duration || track.duration);
      });

      audio.addEventListener("ended", () => {
        if (track.is_mantra_loopable) {
          setCompletedLoops(prev => {
            const next = prev + 1;
            if (loopCountSetting === "infinite" || next < loopCountSetting) {
              audio.currentTime = 0;
              audio.play().catch(() => {});
              return next;
            } else {
              setIsPlaying(false);
              stopAmbient();
              return next;
            }
          });
        } else {
          setIsPlaying(false);
          stopAmbient();
        }
      });

      setIsPlaying(true);
      audio.play().catch(() => {});
      startAmbient();
    } else {
      setIsPlaying(true);
      startAmbient();
    }
  };

  const startAmbient = () => {
    if (ambientBells > 0) bellsAudioRef.current?.play().catch(() => {});
    if (ambientRain > 0) rainAudioRef.current?.play().catch(() => {});
    if (ambientConch > 0) conchAudioRef.current?.play().catch(() => {});
    if (ambientForest > 0) forestAudioRef.current?.play().catch(() => {});
  };

  const stopAmbient = () => {
    bellsAudioRef.current?.pause();
    rainAudioRef.current?.pause();
    conchAudioRef.current?.pause();
    forestAudioRef.current?.pause();
  };

  const togglePlay = () => {
    if (activeTrack && (isSpotifyTrack(activeTrack.url) || isYoutubeTrack(activeTrack.url))) {
      if (isPlaying) {
        stopAmbient();
        setIsPlaying(false);
      } else {
        startAmbient();
        setIsPlaying(true);
      }
      return;
    }

    if (!mainAudioRef.current) return;
    
    if (isPlaying) {
      mainAudioRef.current.pause();
      stopAmbient();
      setIsPlaying(false);
    } else {
      mainAudioRef.current.play().catch(() => {});
      startAmbient();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!mainAudioRef.current) return;
    const seekTime = parseFloat(e.target.value);
    mainAudioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const translateLyrics = async () => {
    if (!activeTrack?.lyrics) return;
    setTranslating(true);
    
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/nada/translate-lyrics`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          lyrics: activeTrack.lyrics,
          deity: activeTrack.deity
        })
      });
      if (response.ok) {
        const data = await response.json();
        setLyricsTranslation(data.translation);
      }
    } catch (e) {
      console.error(e);
    }
    setTranslating(false);
  };

  const toggleFavorite = async (trackId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      await fetch(`${getApiUrl()}/api/v1/nada/tracks/${trackId}/favorite`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
    } catch (e) {
      console.error(e);
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${mins}:${s < 10 ? "0" : ""}${s}`;
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
      console.error("Error loading graph:", e);
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
      setSeedError("Authorization token missing.");
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
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        alert("Crawler discovery sequence triggered.");
        setTimeout(fetchCrawlQueueStatus, 1500);
      } else {
        alert("Trigger rejected.");
      }
    } catch (e) {
      alert("Network error.");
    }
    setTriggerLoading(false);
  };

  // Physics Simulation effect
  useEffect(() => {
    if (graphData.nodes.length === 0) return;
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
    const k = 0.075;
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

  const getNodeColor = (type: string) => {
    switch (type) {
      case "deity": return "#FF9F1C"; 
      case "guru":
      case "speaker": return "#E07A5F"; 
      case "scripture": return "#2EC4B6"; 
      case "concept":
      case "tradition": return "#8338EC"; 
      case "audio": return "#06B6D4"; 
      default: return "#6B7280";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-card/80 to-background border border-sacred-border rounded-xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <Music className="h-6 w-6 text-saffron" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Garuda Nada</h2>
            <span className="text-[10px] bg-saffron/10 border border-saffron/20 text-saffron font-bold px-2 py-0.5 rounded-full uppercase font-mono">
              Spiritual Audio Ingestion
            </span>
          </div>
          <p className="text-xs text-muted-sacred max-w-2xl leading-relaxed">
            Immersive dharmic audio workstation. Stream chants, bhajans, and Vedic hymns discovered from temple sitemaps, 
            Archive.org libraries, and public RSS feeds. Custom loop counts for Japam and ambient temple mixtures.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Columns: Track List & Search Workstation */}
        <div className="lg:col-span-2 space-y-6">

          {/* Workstation Tab Switcher */}
          <div className="flex gap-1.5 p-1 bg-card/65 border border-sacred-border rounded-lg max-w-md">
            <button
              onClick={() => setActiveTab("tracks")}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all cursor-pointer ${
                activeTab === "tracks" ? "bg-saffron text-background shadow" : "text-muted-sacred hover:text-foreground"
              }`}
            >
              <Music className="h-4 w-4" />
              Tracks Feed
            </button>
            <button
              onClick={() => { setActiveTab("graph"); fetchGraphData(); }}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all cursor-pointer ${
                activeTab === "graph" ? "bg-saffron text-background shadow" : "text-muted-sacred hover:text-foreground"
              }`}
            >
              <Network className="h-4 w-4" />
              Nada Graph
            </button>
            <button
              onClick={() => { setActiveTab("crawl"); fetchCrawlQueueStatus(); }}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all cursor-pointer ${
                activeTab === "crawl" ? "bg-saffron text-background shadow" : "text-muted-sacred hover:text-foreground"
              }`}
            >
              <Database className="h-4 w-4" />
              Crawler Queue
            </button>
          </div>
          
          {/* Render Active Tab Content */}
          {activeTab === "tracks" && (
            <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-4">
              <form onSubmit={handleSearch} className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-sacred" />
                  <input 
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search chants, mantras, kirtans, deities (e.g. Shiva, Krishna)..."
                    className="w-full bg-background border border-sacred-border rounded-lg pl-9 pr-4 py-2 text-xs text-foreground focus:outline-none focus:border-saffron/40 font-medium"
                  />
                </div>
                <button 
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className={`border border-sacred-border px-3 rounded-lg flex items-center justify-center cursor-pointer transition-colors ${showFilters ? "bg-saffron/10 border-saffron/40 text-saffron" : "bg-background text-muted-sacred hover:text-foreground"}`}
                >
                  <Sliders className="h-3.5 w-3.5" />
                </button>
                <button 
                  type="submit"
                  className="bg-saffron hover:bg-saffron-dim text-background text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer"
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
                    className="overflow-hidden border-t border-sacred-border/60 pt-3.5 space-y-4"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Tradition dropdown */}
                      <div className="space-y-1.5">
                        <label className="text-[10px] uppercase font-bold tracking-wider text-muted-sacred">Tradition Filter</label>
                        <select 
                          value={tradition}
                          onChange={(e) => { setTradition(e.target.value); triggerSearch(searchQuery, e.target.value); }}
                          className="w-full bg-background border border-sacred-border text-xs rounded-lg px-3 py-1.5 text-foreground focus:outline-none focus:border-saffron/30 font-medium"
                        >
                          <option value="All">All Traditions</option>
                          <option value="Vaishnavism">Vaishnavism</option>
                          <option value="Shaivism">Shaivism</option>
                          <option value="Shaktism">Shaktism</option>
                          <option value="Smarta">Smarta</option>
                          <option value="Advaita">Advaita Vedanta</option>
                          <option value="Dvaita">Dvaita Vedanta</option>
                          <option value="ISKCON">ISKCON</option>
                          <option value="Yoga">Yoga</option>
                        </select>
                      </div>

                      {/* Authenticity threshold slider */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px] font-bold text-muted-sacred uppercase tracking-wider">
                          <span>Min Authenticity Audit</span>
                          <span className="text-saffron font-mono">{minAuthenticity}%</span>
                        </div>
                        <input 
                          type="range"
                          min={0}
                          max={100}
                          step={5}
                          value={minAuthenticity}
                          onChange={(e) => { setMinAuthenticity(parseInt(e.target.value)); triggerSearch(searchQuery, undefined, undefined, parseInt(e.target.value)); }}
                          className="w-full h-1 bg-background border border-sacred-border rounded-lg appearance-none cursor-pointer accent-saffron"
                        />
                      </div>
                    </div>

                    <div className="flex justify-between items-center bg-background/30 p-2.5 rounded-lg border border-sacred-border/40">
                      {/* Multilingual toggle */}
                      <label className="flex items-center gap-2.5 cursor-pointer select-none">
                        <input 
                          type="checkbox"
                          checked={expandMultilingual}
                          onChange={(e) => { setExpandMultilingual(e.target.checked); triggerSearch(searchQuery, undefined, undefined, undefined, e.target.checked); }}
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

              {/* Category Tabs */}
              <div className="flex gap-1.5 border-b border-sacred-border pb-3 overflow-x-auto">
                {["All", "Mantra", "Chant", "Kirtan", "Meditation", "Bhajan"].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => { setCategory(cat); fetchTracks(cat); }}
                    className={`text-[10px] uppercase tracking-wider font-semibold px-3 py-1.5 rounded-md transition-colors cursor-pointer ${
                      category === cat ? "bg-saffron text-background shadow" : "bg-background text-muted-sacred hover:text-foreground"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Track rows */}
              <div className="space-y-2 max-h-[45vh] overflow-y-auto pr-1">
                {loading ? (
                  <div className="text-center py-8 text-xs text-muted-sacred animate-pulse flex flex-col items-center justify-center gap-2">
                    <RefreshCw className="h-4 w-4 text-saffron animate-spin" />
                    <span>Sourcing devotional audios...</span>
                  </div>
                ) : tracks.length === 0 ? (
                  <div className="text-center py-8 text-xs text-muted-sacred">No tracks found. Search online!</div>
                ) : (
                  tracks.map((t) => (
                    <div 
                      key={t.id || t.url}
                      className={`flex items-center justify-between p-3 rounded-lg border transition-colors cursor-pointer group ${
                        ((activeTrack?.id && activeTrack.id === t.id) || (activeTrack?.url === t.url)) ? "bg-saffron/5 border-saffron/30" : "bg-background/40 border-sacred-border hover:bg-card-hover"
                      }`}
                    >
                      <div className="flex items-center gap-3 flex-1" onClick={() => selectTrack(t)}>
                        <div className="h-8 w-8 rounded bg-card flex items-center justify-center border border-sacred-border group-hover:border-saffron/30 transition-colors">
                          {((activeTrack?.id && activeTrack.id === t.id) || (activeTrack?.url === t.url)) && isPlaying ? (
                            <span className="flex gap-0.5 items-end h-3">
                              <span className="w-0.5 h-3 bg-saffron rounded animate-[pulse_1s_infinite]" />
                              <span className="w-0.5 h-1.5 bg-saffron rounded animate-[pulse_0.7s_infinite]" />
                              <span className="w-0.5 h-2 bg-saffron rounded animate-[pulse_1.2s_infinite]" />
                            </span>
                          ) : (
                            <Play className="h-3.5 w-3.5 text-muted-sacred group-hover:text-saffron" />
                          )}
                        </div>
                        <div>
                          <h4 className="text-xs font-semibold text-foreground group-hover:text-saffron transition-colors">{t.title}</h4>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted-sacred">{t.artist}</span>
                            {t.authenticity_score !== undefined && t.authenticity_score > 0 && (
                              <span className="text-[8px] bg-saffron/10 border border-saffron/15 text-saffron px-1 rounded font-bold font-mono">
                                Score: {t.authenticity_score}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-[10px] text-muted-sacred font-medium">
                        {t.url && isSpotifyTrack(t.url) && (
                          <span className="bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 px-1.5 py-0.5 rounded font-mono text-[8px] uppercase">
                            Spotify
                          </span>
                        )}
                        {t.url && isYoutubeTrack(t.url) && (
                          <span className="bg-red-950/40 border border-red-500/30 text-red-400 px-1.5 py-0.5 rounded font-mono text-[8px] uppercase">
                            YouTube
                          </span>
                        )}
                        {t.spiritual_tradition && <span className="bg-saffron/5 border border-saffron/10 text-saffron px-1.5 py-0.2 rounded font-mono text-[8px] uppercase">{t.spiritual_tradition}</span>}
                        <span className="bg-card border border-sacred-border px-1.5 py-0.2 rounded font-mono text-[9px] uppercase">{t.category}</span>
                        <span>{formatTime(t.duration)}</span>
                        <button 
                          onClick={(e) => { e.stopPropagation(); toggleFavorite(t.id); }}
                          className="text-muted-sacred hover:text-saffron cursor-pointer"
                        >
                          <Heart className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Spiritual Nada Graph */}
          {activeTab === "graph" && (
            <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-4">
              <div className="flex flex-col md:flex-row justify-between md:items-center gap-2 border-b border-sacred-border/60 pb-3">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-saffron">Spiritual Nada Graph</h3>
                  <p className="text-[10px] text-muted-sacred">
                    Explore the relationships between deities, scriptures, traditions, and audio tracks. Click to load search feeds.
                  </p>
                </div>
                <button
                  onClick={fetchGraphData}
                  className="self-start md:self-auto text-[9px] uppercase tracking-wider font-semibold border border-sacred-border hover:bg-card-hover text-muted-sacred px-2 py-1 rounded flex items-center gap-1"
                >
                  <RefreshCw className="h-3 w-3" /> Refresh Graph
                </button>
              </div>

              {/* Force Graph SVG */}
              <div className="relative border border-sacred-border rounded-xl bg-[#090a0c] overflow-hidden select-none">
                {graphData.nodes.length === 0 ? (
                  <div className="h-96 flex items-center justify-center text-xs text-muted-sacred animate-pulse">
                    Graph index loading...
                  </div>
                ) : (
                  <svg
                    ref={svgRef}
                    viewBox="0 0 800 500"
                    className="w-full h-auto max-h-[50vh] cursor-grab active:cursor-grabbing"
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                  >
                    {/* Links */}
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

                    {/* Nodes */}
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
                          setActiveTab("tracks");
                          triggerSearch(node.name);
                        }}
                      >
                        <circle
                          r={node.type === "audio" ? 6 : 9}
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

                {/* Graph Tooltip */}
                {hoveredNode && (
                  <div className="absolute bottom-4 left-4 right-4 md:right-auto md:w-80 bg-black/90 border border-sacred-border p-3 rounded-lg shadow-xl text-xs space-y-1 pointer-events-none backdrop-blur-md">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-foreground">{hoveredNode.name}</span>
                      <span className="text-[8px] uppercase tracking-widest font-mono font-bold px-1.5 py-0.5 rounded bg-saffron/10 border border-saffron/20 text-saffron">
                        {hoveredNode.type}
                      </span>
                    </div>
                    {hoveredNode.description && (
                      <p className="text-muted-sacred text-[11px] leading-relaxed pt-1">
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
                <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#2EC4B6" }}></span> Scripture</div>
                <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#8338EC" }}></span> Tradition</div>
                <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full block" style={{ backgroundColor: "#06B6D4" }}></span> Audio Node</div>
              </div>
            </div>
          )}

          {/* Tab 3: Crawl Queue Dashboard */}
          {activeTab === "crawl" && (
            <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Crawler status</span>
                  <span className="text-xs font-bold text-emerald-500 mt-1 block uppercase font-mono animate-pulse">Online</span>
                </div>
                <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Queue Length</span>
                  <span className="text-lg font-bold text-saffron mt-1 block font-mono">{queueStats.pending || 0}</span>
                </div>
                <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Processing</span>
                  <span className="text-lg font-bold text-amber-500 mt-1 block font-mono">{queueStats.processing || 0}</span>
                </div>
                <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Completed</span>
                  <span className="text-lg font-bold text-emerald-600 mt-1 block font-mono">{queueStats.completed || 0}</span>
                </div>
                <div className="bg-background border border-sacred-border p-4 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-muted-sacred block">Failed</span>
                  <span className="text-lg font-bold text-red-500 mt-1 block font-mono">{queueStats.failed || 0}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Seed URL form */}
                <div className="md:col-span-1 bg-background/50 border border-sacred-border p-4 rounded-xl space-y-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-saffron flex items-center gap-1.5">
                    <Plus className="h-4 w-4" /> Queue Seed URL
                  </span>
                  
                  <form onSubmit={handleAddSeed} className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-[9px] uppercase font-bold text-muted-sacred">Crawl target URL</label>
                      <input 
                        type="text"
                        value={newSeedUrl}
                        onChange={(e) => setNewSeedUrl(e.target.value)}
                        placeholder="e.g. RSS Feed link or ashram URL"
                        className="w-full bg-card border border-sacred-border text-xs rounded px-2.5 py-1.5 text-foreground focus:outline-none"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[9px] uppercase font-bold text-muted-sacred">Source Type</label>
                      <select 
                        value={newSourceType}
                        onChange={(e) => setNewSourceType(e.target.value)}
                        className="w-full bg-card border border-sacred-border text-xs rounded px-2.5 py-1.5 text-foreground focus:outline-none"
                      >
                        <option value="podcast_feed">Podcast RSS Feed</option>
                        <option value="youtube_channel">YouTube Channel</option>
                        <option value="youtube_playlist">YouTube Playlist</option>
                        <option value="archive_org">Archive.org Search</option>
                        <option value="sitemap">Website XML Sitemap</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[9px] uppercase font-bold text-muted-sacred">Priority (0-10)</label>
                      <input 
                        type="number"
                        min={0}
                        max={10}
                        value={newPriority}
                        onChange={(e) => setNewPriority(parseInt(e.target.value) || 0)}
                        className="w-full bg-card border border-sacred-border text-xs rounded px-2.5 py-1.5 text-foreground focus:outline-none"
                      />
                    </div>

                    {seedError && <p className="text-[9px] font-bold text-red-400">{seedError}</p>}
                    {seedSuccess && <p className="text-[9px] font-bold text-emerald-400">{seedSuccess}</p>}

                    <button
                      type="submit"
                      className="w-full bg-saffron hover:bg-saffron-dim text-background text-xs font-bold py-2 rounded transition-colors cursor-pointer"
                    >
                      Queue Audio Target
                    </button>
                  </form>

                  <div className="pt-2 border-t border-sacred-border/60">
                    <button
                      onClick={handleTriggerCrawl}
                      disabled={triggerLoading}
                      className="w-full bg-card-hover border border-sacred-border text-muted-sacred hover:text-foreground text-xs font-semibold py-2 rounded transition-colors cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${triggerLoading ? "animate-spin" : ""}`} />
                      {triggerLoading ? "Activating Crawler..." : "Trigger Discovery Cycle"}
                    </button>
                  </div>
                </div>

                {/* History logs */}
                <div className="md:col-span-2 bg-background/50 border border-sacred-border p-4 rounded-xl flex flex-col overflow-hidden">
                  <span className="text-xs font-bold uppercase tracking-wider text-saffron flex items-center gap-1.5 mb-3.5">
                    <Activity className="h-4 w-4" /> Discovery Execution Logs
                  </span>
                  
                  <div className="overflow-x-auto flex-1">
                    <table className="w-full text-[10px] text-left">
                      <thead>
                        <tr className="border-b border-sacred-border text-muted-sacred font-bold text-[8px] uppercase tracking-wider">
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
                            <td colSpan={5} className="py-8 text-center text-muted-sacred italic">No crawl records found.</td>
                          </tr>
                        ) : (
                          crawlHistory.map((h, idx) => (
                            <tr key={idx} className="hover:bg-card/25 transition-colors">
                              <td className="py-2 pr-2 max-w-[140px] truncate font-mono text-[9px] text-foreground" title={h.url}>
                                {h.url}
                              </td>
                              <td className="py-2 px-2 text-muted-sacred font-mono text-[8px] uppercase">{h.source_type}</td>
                              <td className="py-2 px-2">
                                <span className={`px-1 rounded text-[8px] font-bold uppercase ${
                                  h.status === "completed" ? "bg-emerald-950 text-emerald-400 border border-emerald-500/20" : "bg-red-950 text-red-400 border border-red-500/20"
                                }`}>
                                  {h.status}
                                </span>
                              </td>
                              <td className="py-2 px-2 text-right font-mono font-bold text-foreground">{h.discovered_count} items</td>
                              <td className="py-2 pl-2 text-right font-mono text-muted-sacred">{h.duration_seconds}s</td>
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

        {/* Right Column: Active Player & Soundscapes */}
        <div className="space-y-6">
          {/* Audio Player Card */}
          <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-4 animate-fade-in">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred">Active Playback</h3>
            
            {activeTrack ? (
              <div className="space-y-4">
                {isSpotifyTrack(activeTrack.url) ? (
                  <div className="space-y-3">
                    <div className="text-center space-y-1 mb-2">
                      <h4 className="text-xs font-bold text-foreground truncate">{activeTrack.title}</h4>
                      <p className="text-[10px] text-muted-sacred">{activeTrack.artist}</p>
                    </div>
                    <iframe 
                      src={`https://open.spotify.com/embed/track/${getSpotifyId(activeTrack.url)}`}
                      width="100%" 
                      height="80" 
                      frameBorder="0" 
                      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                      loading="lazy"
                      className="rounded-lg border border-sacred-border/50"
                    ></iframe>
                    <div className="flex items-center justify-between bg-background/40 border border-sacred-border/60 rounded-lg p-2.5 text-[10px]">
                      <span className="text-muted-sacred font-medium">Ambient Mixer Overlay</span>
                      <button 
                        onClick={togglePlay}
                        className="px-2 py-0.5 bg-saffron/10 border border-saffron/20 hover:bg-saffron text-saffron hover:text-background text-[9px] uppercase font-bold rounded tracking-wide transition-colors cursor-pointer"
                      >
                        {isPlaying ? "Mute Ambient" : "Activate Ambient"}
                      </button>
                    </div>
                  </div>
                ) : isYoutubeTrack(activeTrack.url) ? (
                  <>
                    {/* Hidden YouTube Video Iframe (Audio Only) */}
                    {isPlaying && (
                      <iframe 
                        src={`https://www.youtube.com/embed/${getYoutubeId(activeTrack.url)}?autoplay=1&mute=0`}
                        width="0" 
                        height="0" 
                        frameBorder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                        style={{ display: "none" }}
                      ></iframe>
                    )}
                    
                    <div className="text-center space-y-1">
                      <div className="h-20 w-20 rounded-full bg-saffron/5 border border-saffron/20 mx-auto flex items-center justify-center saffron-glow animate-[spin_8s_linear_infinite]" style={{ animationPlayState: isPlaying ? 'running' : 'paused' }}>
                        <Music className="h-8 w-8 text-saffron" />
                      </div>
                      <h4 className="text-sm font-bold text-foreground mt-2">{activeTrack.title}</h4>
                      <p className="text-xs text-muted-sacred">{activeTrack.artist}</p>
                    </div>

                    {/* Progress indicator */}
                    <div className="space-y-1">
                      <div className="w-full h-1 bg-background rounded-lg relative overflow-hidden">
                        <div className={`h-full bg-saffron transition-all duration-1000 ${isPlaying ? "w-full" : "w-0"}`} style={{ transitionDuration: `${activeTrack.duration}s`, transitionTimingFunction: 'linear' }}></div>
                      </div>
                      <div className="flex justify-between text-[9px] font-mono text-muted-sacred">
                        <span>YouTube Devotional Audio</span>
                        <span>{formatTime(activeTrack.duration)}</span>
                      </div>
                    </div>

                    {/* Control Panel */}
                    <div className="flex justify-center items-center gap-6">
                      <button 
                        onClick={togglePlay}
                        className="h-10 w-10 bg-saffron text-background rounded-full flex items-center justify-center hover:bg-saffron-dim transition-colors cursor-pointer animate-[pulse_3s_infinite]"
                      >
                        {isPlaying ? <Pause className="h-5 w-5 fill-current" /> : <Play className="h-5 w-5 fill-current ml-0.5" />}
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-center space-y-1">
                      <div className="h-20 w-20 rounded-full bg-saffron/5 border border-saffron/20 mx-auto flex items-center justify-center saffron-glow">
                        <Music className="h-8 w-8 text-saffron" />
                      </div>
                      <h4 className="text-sm font-bold text-foreground mt-2">{activeTrack.title}</h4>
                      <p className="text-xs text-muted-sacred">{activeTrack.artist}</p>
                    </div>

                    {/* Progress bar */}
                    <div className="space-y-1">
                      <input 
                        type="range"
                        min={0}
                        max={duration || 100}
                        value={currentTime}
                        onChange={handleSeek}
                        className="w-full h-1 bg-background rounded-lg appearance-none cursor-pointer accent-saffron"
                      />
                      <div className="flex justify-between text-[9px] font-mono text-muted-sacred">
                        <span>{formatTime(currentTime)}</span>
                        <span>{formatTime(duration)}</span>
                      </div>
                    </div>

                    {/* Control Panel */}
                    <div className="flex justify-center items-center gap-6">
                      {activeTrack.is_mantra_loopable && (
                        <div className="text-center">
                          <span className="text-[8px] uppercase text-muted-sacred block">Completed</span>
                          <span className="text-xs font-mono font-bold text-saffron">{completedLoops} / {loopCountSetting === "infinite" ? "∞" : loopCountSetting}</span>
                        </div>
                      )}

                      <button 
                        onClick={togglePlay}
                        className="h-10 w-10 bg-saffron text-background rounded-full flex items-center justify-center hover:bg-saffron-dim transition-colors cursor-pointer"
                      >
                        {isPlaying ? <Pause className="h-5 w-5 fill-current" /> : <Play className="h-5 w-5 fill-current ml-0.5" />}
                      </button>

                      {activeTrack.is_mantra_loopable && (
                        <div className="flex flex-col items-center">
                          <span className="text-[8px] uppercase text-muted-sacred mb-0.5">Japam Loops</span>
                          <select 
                            value={loopCountSetting}
                            onChange={(e) => setLoopCountSetting(e.target.value === "infinite" ? "infinite" : parseInt(e.target.value))}
                            className="bg-background border border-sacred-border text-[9px] font-bold text-saffron rounded px-1 focus:outline-none"
                          >
                            <option value={11}>11 times</option>
                            <option value={21}>21 times</option>
                            <option value={108}>108 times</option>
                            <option value="infinite">Infinite (∞)</option>
                          </select>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="flex h-36 items-center justify-center border border-dashed border-sacred-border rounded-lg text-xs text-muted-sacred">
                Select a track to play
              </div>
            )}
          </div>

          {/* Ambient sound mixer */}
          <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-saffron animate-pulse" />
              <span>Temple Soundscape Mixer</span>
            </h3>

            <div className="space-y-3.5">
              <div className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-muted-sacred">Temple Bells</span>
                  <span className="font-mono text-saffron">{Math.round(ambientBells * 100)}%</span>
                </div>
                <input 
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={ambientBells}
                  onChange={(e) => setAmbientBells(parseFloat(e.target.value))}
                  className="w-full h-1 bg-background rounded-lg appearance-none cursor-pointer accent-saffron"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-muted-sacred">Deep Rain</span>
                  <span className="font-mono text-saffron">{Math.round(ambientRain * 100)}%</span>
                </div>
                <input 
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={ambientRain}
                  onChange={(e) => setAmbientRain(parseFloat(e.target.value))}
                  className="w-full h-1 bg-background rounded-lg appearance-none cursor-pointer accent-saffron"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-muted-sacred">Sacred Conch</span>
                  <span className="font-mono text-saffron">{Math.round(ambientConch * 100)}%</span>
                </div>
                <input 
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={ambientConch}
                  onChange={(e) => setAmbientConch(parseFloat(e.target.value))}
                  className="w-full h-1 bg-background rounded-lg appearance-none cursor-pointer accent-saffron"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-muted-sacred">Morning Forest Birds</span>
                  <span className="font-mono text-saffron">{Math.round(ambientForest * 100)}%</span>
                </div>
                <input 
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={ambientForest}
                  onChange={(e) => setAmbientForest(parseFloat(e.target.value))}
                  className="w-full h-1 bg-background rounded-lg appearance-none cursor-pointer accent-saffron"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom lyrics translator segment */}
      {activeTrack && (activeTrack.lyrics || lyricsTranslation) && (
        <div className="bg-card border border-sacred-border rounded-xl p-5 space-y-4">
          <div className="flex justify-between items-center border-b border-sacred-border pb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-saffron" />
              <span>Lyrics Contemplation & Sanskrit Breakdown</span>
            </h3>
            {activeTrack.lyrics && !lyricsTranslation && (
              <button 
                onClick={translateLyrics}
                disabled={translating}
                className="text-[10px] bg-saffron/10 border border-saffron/20 hover:bg-saffron text-saffron hover:text-background px-3 py-1 rounded font-semibold cursor-pointer"
              >
                {translating ? "Translating hymns..." : "AI Word-by-Word Breakdown"}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <span className="text-[10px] uppercase tracking-wider text-muted-sacred font-semibold">Devotional Hymn (Original)</span>
              <pre className="text-xs text-foreground bg-background/50 p-4 rounded-lg border border-sacred-border font-sans whitespace-pre-wrap leading-relaxed">
                {activeTrack.lyrics || "Lyrics not available."}
              </pre>
            </div>
            
            <div className="space-y-2">
              <span className="text-[10px] uppercase tracking-wider text-muted-sacred font-semibold">Dharmic Translation & Commentary</span>
              <div className="text-xs text-muted-sacred bg-background/50 p-4 rounded-lg border border-sacred-border leading-relaxed min-h-[150px] whitespace-pre-wrap">
                {translating ? (
                  <span className="animate-pulse">Retrieving spiritual insights from local Ollama model...</span>
                ) : lyricsTranslation ? (
                  lyricsTranslation
                ) : activeTrack.meaning ? (
                  activeTrack.meaning
                ) : (
                  "Click 'AI Word-by-Word Breakdown' to analyze the deeper metaphysical significance of the hymn."
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
