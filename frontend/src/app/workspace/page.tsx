"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { getApiUrl } from "@/utils/api";
import { 
  Network, 
  FileText, 
  Plus, 
  Trash, 
  Calendar, 
  CheckSquare, 
  Square,
  Sparkles,
  Link as LinkIcon,
  Save,
  Tag,
  PenTool,
  Clock
} from "lucide-react";

interface Note {
  id: number;
  title: string;
  content: string;
  category: string;
  ai_summary?: string;
  tags?: string;
  created_at: string;
  updated_at: string;
}

interface GraphNode {
  id: number;
  title: string;
  category: string;
  tags: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface GraphLink {
  id: number;
  source: number;
  target: number;
  type: string;
}

interface DharmicTask {
  id: number;
  title: string;
  details?: string;
  category: string;
  target_date: string;
  due_time?: string;
  is_completed: boolean;
  repeat_frequency: string;
}

export default function ConsciousnessWorkspace() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  
  // Note editor inputs
  const [editorTitle, setEditorTitle] = useState("");
  const [editorContent, setEditorContent] = useState("");
  const [editorCategory, setEditorCategory] = useState("Realization");
  const [editorTags, setEditorTags] = useState("");
  const [savingNote, setSavingNote] = useState(false);

  // Link notes inputs
  const [targetLinkId, setTargetLinkId] = useState<number | "">("");

  // Graph Data state
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphLinks, setGraphLinks] = useState<GraphLink[]>([]);
  const graphContainerRef = useRef<SVGSVGElement | null>(null);
  const [draggedNodeId, setDraggedNodeId] = useState<number | null>(null);

  // Task list states
  const [tasks, setTasks] = useState<DharmicTask[]>([]);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskCategory, setNewTaskCategory] = useState("Chanting");
  const [newTaskDueTime, setNewTaskDueTime] = useState("05:00 AM");

  useEffect(() => {
    fetchNotes();
    fetchGraphData();
    fetchTasks();
  }, []);

  // --- Network Physics Simulator ---
  useEffect(() => {
    if (graphNodes.length === 0) return;

    let animationFrameId: number;
    const width = 400;
    const height = 280;
    const k = 0.08;      // Spring constant
    const rep = 800;    // Repulsion constant
    const damping = 0.85; // Friction

    const tick = () => {
      setGraphNodes((prevNodes) => {
        const nodes = prevNodes.map(n => ({ ...n }));
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        // Calculate Repulsion forces (all pairs)
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const n1 = nodes[i];
            const n2 = nodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const distSq = dx * dx + dy * dy || 1;
            const dist = Math.sqrt(distSq);
            
            if (dist < 150) {
              const force = rep / (distSq * dist);
              const fx = dx * force;
              const fy = dy * force;

              if (n1.id !== draggedNodeId) {
                n1.vx -= fx;
                n1.vy -= fy;
              }
              if (n2.id !== draggedNodeId) {
                n2.vx += fx;
                n2.vy += fy;
              }
            }
          }
        }

        // Calculate Link attraction forces
        graphLinks.forEach((link) => {
          const s = nodeMap.get(link.source);
          const t = nodeMap.get(link.target);
          if (s && t) {
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = k * (dist - 80); // Rest length of 80
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (s.id !== draggedNodeId) {
              s.vx += fx;
              s.vy += fy;
            }
            if (t.id !== draggedNodeId) {
              t.vx -= fx;
              t.vy -= fy;
            }
          }
        });

        // Apply forces, gravity to center & constraints
        nodes.forEach((n) => {
          if (n.id === draggedNodeId) return;

          // Gravity pull to center
          const cx = width / 2;
          const cy = height / 2;
          n.vx += (cx - n.x) * 0.005;
          n.vy += (cy - n.y) * 0.005;

          // Update position
          n.x += n.vx;
          n.y += n.vy;

          // Damping
          n.vx *= damping;
          n.vy *= damping;

          // Keep in bounds
          n.x = Math.max(20, Math.min(width - 20, n.x));
          n.y = Math.max(20, Math.min(height - 20, n.y));
        });

        return nodes;
      });

      animationFrameId = requestAnimationFrame(tick);
    };

    animationFrameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrameId);
  }, [graphLinks, draggedNodeId, graphNodes.length]);

  // --- API Handlers ---
  const fetchNotes = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/notes`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setNotes(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchGraphData = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/notes/graph`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGraphLinks(data.links);
        
        // Initialize positions if not matching current count
        const width = 400;
        const height = 280;
        const mapped = data.nodes.map((n: any, idx: number) => {
          // Keep existing node positions if they exist
          const oldNode = graphNodes.find(gn => gn.id === n.id);
          if (oldNode) return oldNode;
          
          const angle = (idx / data.nodes.length) * 2 * Math.PI;
          return {
            ...n,
            x: width / 2 + Math.cos(angle) * 80,
            y: height / 2 + Math.sin(angle) * 80,
            vx: 0,
            vy: 0
          };
        });
        setGraphNodes(mapped);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchTasks = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/tasks`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createNote = () => {
    setSelectedNote(null);
    setEditorTitle("Untitled Note");
    setEditorContent("");
    setEditorCategory("Realization");
    setEditorTags("");
  };

  const selectNote = (note: Note) => {
    setSelectedNote(note);
    setEditorTitle(note.title);
    setEditorContent(note.content || "");
    setEditorCategory(note.category || "Realization");
    setEditorTags(note.tags || "");
  };

  const saveNote = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    
    setSavingNote(true);
    const body = {
      title: editorTitle,
      content: editorContent,
      category: editorCategory,
      tags: editorTags
    };

    try {
      let response;
      if (selectedNote) {
        // Update
        response = await fetch(`${getApiUrl()}/api/v1/workspace/notes/${selectedNote.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify(body)
        });
      } else {
        // Create
        response = await fetch(`${getApiUrl()}/api/v1/workspace/notes`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify(body)
        });
      }

      if (response.ok) {
        const saved = await response.json();
        setSelectedNote(saved);
        fetchNotes();
        fetchGraphData();
      }
    } catch (e) {
      console.error(e);
    }
    setSavingNote(false);
  };

  const deleteNote = async (noteId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/notes/${noteId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        if (selectedNote?.id === noteId) {
          createNote();
        }
        fetchNotes();
        fetchGraphData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const linkNote = async () => {
    if (!selectedNote || !targetLinkId) return;
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/notes/links`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          source_note_id: selectedNote.id,
          target_note_id: Number(targetLinkId),
          link_type: "ref"
        })
      });

      if (response.ok) {
        setTargetLinkId("");
        fetchGraphData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // --- Task Operations ---
  const addTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          title: newTaskTitle,
          category: newTaskCategory,
          due_time: newTaskDueTime
        })
      });

      if (response.ok) {
        setNewTaskTitle("");
        fetchTasks();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const toggleTask = async (task: DharmicTask) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/tasks/${task.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          is_completed: !task.is_completed
        })
      });
      if (response.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteTask = async (taskId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/workspace/tasks/${taskId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // --- SVG drag handlers ---
  const handleMouseDown = (nodeId: number, e: React.MouseEvent) => {
    setDraggedNodeId(nodeId);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (draggedNodeId === null || !graphContainerRef.current) return;
    const svgRect = graphContainerRef.current.getBoundingClientRect();
    const x = e.clientX - svgRect.left;
    const y = e.clientY - svgRect.top;
    
    setGraphNodes((prev) => 
      prev.map((n) => (n.id === draggedNodeId ? { ...n, x, y, vx: 0, vy: 0 } : n))
    );
  };

  const handleMouseUp = () => {
    setDraggedNodeId(null);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-auto lg:h-[80vh]">
      {/* Col 1: Notes Sidebar (List) */}
      <div className="lg:col-span-3 bg-card border border-sacred-border rounded-xl p-4 flex flex-col h-[400px] lg:h-full overflow-hidden">
        <div className="flex justify-between items-center mb-4 border-b border-sacred-border pb-2.5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred flex items-center gap-1.5">
            <FileText className="h-4 w-4 text-saffron" />
            <span>Spiritual Notes</span>
          </h3>
          <button 
            onClick={createNote}
            className="p-1 hover:bg-card-hover border border-sacred-border rounded text-saffron transition-colors cursor-pointer"
            title="Create Note"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        {/* Notes list */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {notes.length === 0 ? (
            <p className="text-[10px] text-muted-sacred italic text-center py-4">No spiritual notes recorded.</p>
          ) : (
            notes.map((n) => (
              <div
                key={n.id}
                onClick={() => selectNote(n)}
                className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                  selectedNote?.id === n.id 
                    ? "bg-saffron/5 border-saffron/30" 
                    : "bg-background/30 border-sacred-border hover:bg-card-hover"
                }`}
              >
                <div className="flex justify-between items-start gap-2">
                  <h4 className="text-xs font-semibold text-foreground line-clamp-1">{n.title}</h4>
                  <button 
                    onClick={(e) => { e.stopPropagation(); deleteNote(n.id); }}
                    className="text-muted-sacred hover:text-overloaded p-0.5 cursor-pointer"
                  >
                    <Trash className="h-3 w-3" />
                  </button>
                </div>
                <p className="text-[10px] text-muted-sacred line-clamp-2 mt-1 leading-relaxed">
                  {n.content || "Empty content"}
                </p>
                <div className="flex justify-between items-center mt-2 text-[9px] text-muted-sacred">
                  <span className="bg-background border border-sacred-border px-1.5 rounded">{n.category}</span>
                  <span className="font-mono">{new Date(n.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Col 2: Markdown Editor */}
      <div className="lg:col-span-5 bg-card border border-sacred-border rounded-xl p-5 flex flex-col h-[450px] lg:h-full overflow-hidden">
        <div className="flex justify-between items-center mb-4 border-b border-sacred-border pb-2.5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred flex items-center gap-1.5">
            <PenTool className="h-4 w-4 text-saffron" />
            <span>Note Editor</span>
          </h3>
          <button 
            onClick={saveNote}
            disabled={savingNote}
            className="flex items-center gap-1.5 bg-saffron hover:bg-saffron-dim text-background text-[11px] font-bold px-3 py-1 rounded-md cursor-pointer disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5" />
            <span>{savingNote ? "Saving..." : "Save Note"}</span>
          </button>
        </div>

        {/* Editor Inputs */}
        <div className="flex-1 flex flex-col space-y-3 overflow-y-auto pr-1">
          <input 
            type="text"
            value={editorTitle}
            onChange={(e) => setEditorTitle(e.target.value)}
            placeholder="Note Title..."
            className="w-full bg-background border border-sacred-border rounded-lg px-3 py-2 text-xs font-bold text-foreground focus:outline-none focus:border-saffron/40"
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[9px] uppercase tracking-wider text-muted-sacred block mb-1">Category</label>
              <select
                value={editorCategory}
                onChange={(e) => setEditorCategory(e.target.value)}
                className="w-full bg-background border border-sacred-border rounded-lg px-2.5 py-1.5 text-xs text-muted-sacred focus:outline-none"
              >
                <option value="Realization">Realization</option>
                <option value="Gita study">Gita Study</option>
                <option value="Upanishads">Upanishad Study</option>
                <option value="Sadhana journal">Sadhana Journal</option>
                <option value="Temple visit">Temple Reflection</option>
              </select>
            </div>
            <div>
              <label className="text-[9px] uppercase tracking-wider text-muted-sacred block mb-1">Tags (comma sep)</label>
              <input 
                type="text"
                value={editorTags}
                onChange={(e) => setEditorTags(e.target.value)}
                placeholder="atman, devotion, karma..."
                className="w-full bg-background border border-sacred-border rounded-lg px-2.5 py-1.5 text-xs text-muted-sacred focus:outline-none"
              />
            </div>
          </div>

          <textarea 
            value={editorContent}
            onChange={(e) => setEditorContent(e.target.value)}
            placeholder="Record your realization, contemplation, or scriptural studies in markdown..."
            className="flex-1 w-full bg-background border border-sacred-border rounded-lg p-3 text-xs text-foreground font-sans focus:outline-none focus:border-saffron/40 resize-none min-h-[180px]"
          />

          {/* AI reflection snippet if exists */}
          {selectedNote?.ai_summary && (
            <div className="bg-saffron/5 border border-saffron/10 rounded-lg p-3 space-y-1">
              <span className="text-[9px] font-semibold text-saffron uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="h-3 w-3 animate-pulse" /> Spiritual Realization Breakdown
              </span>
              <p className="text-[11px] text-muted-sacred leading-relaxed">{selectedNote.ai_summary}</p>
            </div>
          )}
        </div>
      </div>

      {/* Col 3: Visualizer Graph & Sadhana tasks */}
      <div className="lg:col-span-4 flex flex-col gap-6 h-auto lg:h-full overflow-hidden">
        {/* Obsidian Link Graph */}
        <div className="bg-card border border-sacred-border rounded-xl p-4 flex flex-col h-[320px] lg:h-1/2 overflow-hidden">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred flex items-center gap-1.5 mb-2.5">
            <Network className="h-4 w-4 text-saffron" />
            <span>Second Brain Link Graph</span>
          </h3>

          <div className="flex-1 bg-background rounded-lg border border-sacred-border relative overflow-hidden">
            <svg
              ref={graphContainerRef}
              className="w-full h-full cursor-grab active:cursor-grabbing"
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              viewBox="0 0 400 280"
            >
              {/* Lines (Links) */}
              {graphLinks.map((link) => {
                const sourceNode = graphNodes.find(n => n.id === link.source);
                const targetNode = graphNodes.find(n => n.id === link.target);
                if (!sourceNode || !targetNode) return null;
                
                return (
                  <line
                    key={link.id}
                    x1={sourceNode.x}
                    y1={sourceNode.y}
                    x2={targetNode.x}
                    y2={targetNode.y}
                    stroke="#e58e26"
                    strokeOpacity={0.25}
                    strokeWidth={1.5}
                  />
                );
              })}

              {/* Circles (Nodes) */}
              {graphNodes.map((node) => {
                const isSelected = selectedNote?.id === node.id;
                
                return (
                  <g key={node.id} className="cursor-pointer">
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isSelected ? 8 : 6}
                      fill={isSelected ? "#e58e26" : "#4a6b5c"}
                      stroke="#0d0b0a"
                      strokeWidth={1.5}
                      onMouseDown={(e) => handleMouseDown(node.id, e)}
                      onClick={() => {
                        const original = notes.find(n => n.id === node.id);
                        if (original) selectNote(original);
                      }}
                    />
                    <text
                      x={node.x}
                      y={node.y - 10}
                      textAnchor="middle"
                      fill="#f4efe6"
                      fontSize={8}
                      fontWeight="bold"
                      className="pointer-events-none select-none bg-black/80 px-1"
                    >
                      {node.title}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Note Linking Drawer */}
            {selectedNote && (
              <div className="absolute bottom-2 left-2 right-2 bg-card border border-sacred-border rounded p-2 flex items-center justify-between gap-2">
                <span className="text-[9px] text-muted-sacred truncate max-w-[120px]">Link {selectedNote.title} to:</span>
                <select
                  value={targetLinkId}
                  onChange={(e) => setTargetLinkId(e.target.value === "" ? "" : Number(e.target.value))}
                  className="bg-background border border-sacred-border text-[9px] text-muted-sacred rounded px-1 py-0.5 focus:outline-none"
                >
                  <option value="">Select note...</option>
                  {notes.filter(n => n.id !== selectedNote.id).map(n => (
                    <option key={n.id} value={n.id}>{n.title}</option>
                  ))}
                </select>
                <button 
                  onClick={linkNote}
                  className="bg-saffron text-background text-[9px] font-bold px-2 py-0.5 rounded cursor-pointer"
                >
                  Link
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Sadhana tasks tracker */}
        <div className="bg-card border border-sacred-border rounded-xl p-4 flex flex-col h-[350px] lg:h-1/2 overflow-hidden">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-sacred flex items-center gap-1.5 mb-2.5">
            <CheckSquare className="h-4 w-4 text-saffron" />
            <span>Sadhana Checklist</span>
          </h3>

          <div className="flex-1 flex flex-col space-y-3 overflow-hidden">
            {/* Quick Add Task */}
            <form onSubmit={addTask} className="flex gap-2">
              <input 
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="New daily sadhana task (e.g. 11 rounds Gayatri Japa)..."
                className="flex-1 bg-background border border-sacred-border rounded px-2.5 py-1.5 text-[10px] text-foreground focus:outline-none"
              />
              <button 
                type="submit"
                className="bg-saffron hover:bg-saffron-dim text-background text-[10px] font-bold px-3 rounded cursor-pointer"
              >
                Add
              </button>
            </form>

            {/* List */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {tasks.length === 0 ? (
                <p className="text-[10px] text-muted-sacred italic text-center py-4">No sadhana tasks set for today.</p>
              ) : (
                tasks.map((t) => (
                  <div 
                    key={t.id}
                    className="flex items-center justify-between p-2 rounded bg-background/40 border border-sacred-border/70 hover:border-saffron/10 transition-colors"
                  >
                    <div className="flex items-center gap-2 flex-1 cursor-pointer" onClick={() => toggleTask(t)}>
                      {t.is_completed ? (
                        <CheckSquare className="h-4 w-4 text-saffron fill-saffron/10" />
                      ) : (
                        <Square className="h-4 w-4 text-muted-sacred" />
                      )}
                      <span className={`text-[11px] ${t.is_completed ? "line-through text-muted-sacred" : "text-foreground font-medium"}`}>
                        {t.title}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[9px] text-muted-sacred">
                      <span className="flex items-center gap-0.5"><Clock className="h-3 w-3" /> {t.due_time || "05:00 AM"}</span>
                      <button 
                        onClick={() => deleteTask(t.id)}
                        className="text-muted-sacred hover:text-overloaded cursor-pointer"
                      >
                        <Trash className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
