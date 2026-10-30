import json

with open("scratch/vps_config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

warp_domains = [
    # --- OpenAI & ChatGPT ---
    "domain:openai.com",
    "domain:chatgpt.com",
    "domain:chat.openai.com",
    "domain:api.openai.com",
    "domain:auth0.openai.com",
    "domain:platform.openai.com",
    "domain:oaistatic.com",
    "domain:oaiusercontent.com",
    "domain:openai.com.cdn.cloudflare.net",
    "domain:challenges.cloudflare.com",
    
    # --- Anthropic & Claude ---
    "domain:anthropic.com",
    "domain:claude.ai",
    "domain:api.anthropic.com",
    "domain:claude.usercontent.com",
    
    # --- Google AI & Gemini ---
    "domain:aistudio.google.com",
    "domain:gemini.google.com",
    "domain:generativelanguage.googleapis.com",
    "domain:makersuite.google.com",
    "domain:alkalimakersuite-pa.clients6.google.com",
    "domain:bard.google.com",
    
    # --- Other AI Tools ---
    "domain:perplexity.ai",
    "domain:copilot.microsoft.com",
    "domain:suno.ai",
    "domain:suno.com",
    "domain:runwayml.com",
    "domain:midjourney.com",
    "domain:elevenlabs.io",
    "domain:cohere.com",
    "domain:deepseek.com",
    
    # --- Streaming & Services with Strict Geo-blocks ---
    "domain:netflix.com",
    "domain:nflxvideo.net",
    "domain:nflxext.com",
    "domain:nflximg.net",
    "domain:nflxso.net",
    "domain:spotify.com",
    "domain:scdn.co",
    "domain:spotifycdn.com",
    "domain:notion.so",
    "domain:notion-static.com",
    "domain:notionusercontent.com",
    "domain:canva.com",
    "domain:canva.dev"
]

for rule in cfg.get("routing", {}).get("rules", []):
    if rule.get("outboundTag") == "warp":
        rule["domain"] = warp_domains

with open("scratch/vps_config_updated.json", "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("Updated config written successfully.")
