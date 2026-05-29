// Client-side YouTube and Spotify spiritual search integration utility

export const BLOCK_LIST = [
  "unboxing", "gaming", "prank", "makeup", "comedy", "funny", "trailer",
  "hip hop", "rap", "pop song", "reaction", "challenge", "meme", "roast",
  "drama", "news", "politics", "cricket", "football", "sports", "movie",
  "web series", "episode", "season", "serial", "teaser", "interview",
  "celebrity", "bollywood", "hollywood", "song remix", "dj remix",
  "horror", "thriller", "action movie", "item song", "love song",
  "cartoon", "cartoons", "animation", "animated", "sonic gang", "nick india",
  "kids club", "kids show", "toy", "toys", "nickelodeon", "voot kids",
  "kinder", "disney", "pogo", "hungama",
  "roast", "standup", "stand up comedy", "tech", "gadget", "phone review",
  "stock market", "crypto", "finance", "business", "startup",
  "kids", "kid", "tv show", "tv serial", "show", "sonic", "nick", "voot", 
  "jiohotstar", "hotstar", "channel", "nursery", "rhymes", "rhyme", "poem", "poems",
  "tv channel", "kids songs", "kids song"
];

export const SPIRITUAL_MUST_CONTAIN = [
  "shiva", "vishnu", "krishna", "rama", "durga", "kali", "lakshmi",
  "saraswati", "ganesh", "ganesha", "hanuman", "murugan", "ayyappa",
  "devi", "shakti", "brahma", "narayana", "venkatesh", "balaji",
  "tirupati", "venkateswara", "radha", "sita", "parvati", "mahadev",
  "shiv", "shambhu", "sambhu", "kartikeya", "subrahmanya", "subramanya",
  "vinayaka", "ganpati", "ganapathi", "ganapati", "muruga", "gayatri",
  "lalitha", "lalita", "bhairav", "bhairava", "dattatreya", "hanumana",
  "saraswathi", "lakshmy", "laxmi",
  "gita", "bhagavad", "upanishad", "veda", "vedic", "ramayana",
  "mahabharata", "mahabharat", "purana", "bhagavatam", "bhagavat",
  "geeta", "ramcharitmanas", "chalisa", "stotram", "stotra",
  "sahasranama", "sahasranamam", "ashtakam", "astakam", "pancharatnam",
  "hrudayam", "hridayam", "lahari", "rudram", "chamakam", "suktam", "sukta",
  "hymn", "hymns", "shloka", "sloka", "shlokas", "slokas", "recitation",
  "reciting", "stuti", "jaap", "naam", "namavali", "upanishads", "vedas",
  "puranas", "slok",
  "bhajan", "kirtan", "mantra", "chant", "puja", "aarti", "arti",
  "meditation", "dhyana", "yoga", "pranayama", "satsang", "pravachan",
  "havan", "homam", "abhishek", "japa", "sadhana", "tapas", "prayers", "prayer",
  "vedanta", "advaita", "dvaita", "bhakti", "karma", "dharma",
  "moksha", "liberation", "enlightenment", "self-realization",
  "spiritual", "spirituality", "divine", "sacred", "devotional",
  "hindu", "hinduism", "sanatan", "dharmic",
  "swami", "guru", "maharaj", "acharya", "sadhu", "sanyasi",
  "ashram", "iskcon", "isha", "art of living", "chinmaya",
  "ramakrishna", "vivekananda", "ramana", "maharshi", "shankara",
  "nisargadatta", "neem karoli", "yogananda", "sivananda", "paramahansa",
  "sadhguru", "osho", "chinmayananda", "krishnamurti", "chidananda"
];

export function isBlocked(title: string, description = "", channel = ""): boolean {
  const text = `${title} ${description} ${channel}`.toLowerCase();
  return BLOCK_LIST.some(word => text.includes(word));
}

export function isSpiritual(title: string, description = ""): boolean {
  const text = `${title} ${description}`.toLowerCase();
  const additional = ["chalisa", "jaap", "stotra", "aarti", "chant", "stotram"];
  return SPIRITUAL_MUST_CONTAIN.some(word => text.includes(word)) || additional.some(word => text.includes(word));
}

export function guessCategory(title: string, description = ""): string {
  const text = `${title} ${description}`.toLowerCase();
  if (["bhajan", "kirtan", "aarti", "stuti", "stotra"].some(k => text.includes(k))) return "Bhakti";
  if (["mantra", "chant", "japa", "108"].some(k => text.includes(k))) return "Chants";
  if (["gita", "bhagavad", "upanishad", "vedanta", "advaita"].some(k => text.includes(k))) return "Vedanta";
  if (["yoga", "pranayama", "asana", "kundalini"].some(k => text.includes(k))) return "Yoga";
  if (["meditation", "dhyana", "mindfulness", "sadhana"].some(k => text.includes(k))) return "Meditation";
  if (["discourse", "lecture", "talk", "pravachan", "satsang"].some(k => text.includes(k))) return "Satsang";
  if (["puja", "ritual", "abhishek", "havan", "homam"].some(k => text.includes(k))) return "Ritual";
  if (["ramayana", "mahabharat", "puranas", "katha", "story"].some(k => text.includes(k))) return "Storytelling";
  return "Satsang";
}

export function parseDuration(durationStr: string): number {
  if (!durationStr) return 0;
  const match = durationStr.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (match) {
    const h = parseInt(match[1] || "0", 10);
    const m = parseInt(match[2] || "0", 10);
    const s = parseInt(match[3] || "0", 10);
    return h * 3600 + m * 60 + s;
  }
  
  // Format MM:SS or HH:MM:SS
  try {
    const parts = durationStr.split(":").map(Number);
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
  } catch (e) {}
  
  return 0;
}

export async function searchYouTubeClient(query: string, apiKey: string, maxResults = 25): Promise<any[]> {
  try {
    const isAlreadySpiritual = isSpiritual(query);
    const search_query = isAlreadySpiritual ? query : `${query} hindu spiritual`;
    const searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(search_query)}&type=video&maxResults=${maxResults + 10}&key=${apiKey}&safeSearch=moderate`;
    
    const response = await fetch(searchUrl);
    if (!response.ok) {
      console.error("YouTube search API failed:", response.statusText);
      return [];
    }
    const data = await response.json();
    const items = data.items || [];
    const videoIds = items
      .map((item: any) => item.id?.videoId)
      .filter((id: string) => !!id);
    
    if (videoIds.length === 0) return [];
    
    // Fetch details
    const detailUrl = `https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet,statistics&id=${videoIds.join(",")}&key=${apiKey}`;
    const detailResponse = await fetch(detailUrl);
    const detailsMap: { [key: string]: any } = {};
    if (detailResponse.ok) {
      const detailData = await detailResponse.json();
      (detailData.items || []).forEach((item: any) => {
        detailsMap[item.id] = item;
      });
    }
    
    const results: any[] = [];
    items.forEach((item: any) => {
      const vidId = item.id?.videoId;
      if (!vidId) return;
      
      const snippet = item.snippet || {};
      const title = snippet.title || "";
      const description = snippet.description || "";
      const channel = snippet.channelTitle || "";
      
      if (isBlocked(title, description, channel) || !isSpiritual(title, description)) {
        return;
      }
      
      const detail = detailsMap[vidId] || {};
      const durationStr = detail.contentDetails?.duration || "";
      const duration = parseDuration(durationStr);
      const thumb = snippet.thumbnails?.high?.url || snippet.thumbnails?.medium?.url || `https://img.youtube.com/vi/${vidId}/hqdefault.jpg`;
      
      results.push({
        youtube_id: vidId,
        title: title,
        description: channel ? `By ${channel}. ${description}` : description,
        duration: duration,
        thumbnail_url: thumb,
        category: guessCategory(title, description),
        channel_name: channel
      });
    });
    
    return results.slice(0, maxResults);
  } catch (e) {
    console.error("Error in client-side YouTube search:", e);
    return [];
  }
}

export async function searchSpotifyClient(query: string, clientId: string, clientSecret: string, limit = 15): Promise<any[]> {
  try {
    const spiritualKeywords = ["bhajan", "mantra", "kirtan", "stotram", "chant", "dharmic", "spiritual", "shiva", "krishna", "devi", "ganesha", "hanuman", "rama", "vedic", "suprabhatam", "chalisa", "jaap"];
    const queryLower = query.toLowerCase();
    const hasSpiritual = spiritualKeywords.some(kw => queryLower.includes(kw));
    const searchQuery = hasSpiritual ? query : `${query} bhajan stotram chant`;
    
    // Client credentials flow
    const tokenUrl = "https://accounts.spotify.com/api/token";
    const creds = btoa(`${clientId}:${clientSecret}`);
    const tokenResponse = await fetch(tokenUrl, {
      method: "POST",
      headers: {
        "Authorization": `Basic ${creds}`,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: "grant_type=client_credentials"
    });
    
    if (!tokenResponse.ok) {
      console.error("Spotify authorization failed:", tokenResponse.statusText);
      return [];
    }
    const tokenData = await tokenResponse.json();
    const token = tokenData.access_token;
    if (!token) return [];
    
    // Search tracks
    const searchUrl = `https://api.spotify.com/v1/search?q=${encodeURIComponent(searchQuery)}&type=track&limit=${limit}`;
    const searchResponse = await fetch(searchUrl, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    if (!searchResponse.ok) {
      console.error("Spotify search query failed:", searchResponse.statusText);
      return [];
    }
    const searchData = await searchResponse.json();
    const items = searchData.tracks?.items || [];
    
    return items.map((item: any) => {
      const trackId = item.id;
      const title = item.name;
      const artists = (item.artists || []).map((a: any) => a.name).join(", ");
      const spotifyUrl = item.external_urls?.spotify || `https://open.spotify.com/track/${trackId}`;
      const durationS = Math.floor((item.duration_ms || 0) / 1000);
      
      let deity: string | null = null;
      for (const d of ["shiva", "krishna", "devi", "rama", "ganesha", "hanuman"]) {
        if (title.toLowerCase().includes(d) || queryLower.includes(d)) {
          deity = d.charAt(0).toUpperCase() + d.slice(1);
          break;
        }
      }
      
      let category = "Bhajan";
      for (const c of ["mantra", "chant", "kirtan", "meditation"]) {
        if (title.toLowerCase().includes(c)) {
          category = c.charAt(0).toUpperCase() + c.slice(1);
          break;
        }
      }
      
      return {
        title: title,
        artist: artists,
        url: spotifyUrl,
        category: category,
        deity: deity || undefined,
        duration: durationS,
        lyrics: `[Spotify Streaming Hymn]\nLyrics study in progress for '${title}'...`,
        meaning: `Contemplate this devotional track: ${title} by ${artists}.`,
        mood_tags: "calm, bhakti",
        spiritual_intensity: 4,
        is_mantra_loopable: ["mantra", "loop", "chant", "108"].some(w => title.toLowerCase().includes(w)),
        audio_source: "spotify",
        authenticity_score: 85
      };
    });
  } catch (e) {
    console.error("Error in client-side Spotify search:", e);
    return [];
  }
}
