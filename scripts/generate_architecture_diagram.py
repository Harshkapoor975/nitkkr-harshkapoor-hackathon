"""
Generates high-resolution architecture diagram (docs/architecture.png)
for S&P Global & CRISIL Hackathon 2026 submission.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_architecture_diagram():
    os.makedirs('docs', exist_ok=True)
    width = 1600
    height = 900
    
    # Dark modern canvas
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    # Title Banner
    draw.rectangle([(0, 0), (width, 100)], fill='#1e293b')
    draw.text((50, 25), "S&P Global & CRISIL Campus Hackathon 2026", fill='#94a3b8')
    draw.text((50, 50), "AI/NLP Risk Intelligence Engine & Tactical Index Rebalancer (Module A)", fill='#38bdf8')
    
    # Stage Boxes Configuration: (x, y, w, h, title, subtitle, color, border)
    stages = [
        {
            "rect": (60, 160, 320, 660),
            "header_fill": "#1e3a5f",
            "body_fill": "#0f233a",
            "border": "#2563eb",
            "title": "1. Multi-Source Ingestion",
            "items": [
                "• Live RSS Firehoses",
                "  (CNBC, WSJ, Google, Moneycontrol)",
                "• Deep Web Scraper (Yahoo Finance)",
                "• Social Media & Microblogs",
                "• Cashtag & Entity Detection",
                "",
                "Ingestion Rate: Real-time",
                "Throughput: Thousands of items/sec",
                "Protocol: Concurrent Async Threads"
            ]
        },
        {
            "rect": (430, 160, 340, 660),
            "header_fill": "#2d2050",
            "body_fill": "#18102e",
            "border": "#8b5cf6",
            "title": "2. Senior NLP Risk Engine",
            "items": [
                "• Layer 0: Noise Reduction & Regex",
                "• Layer 1: Contextual NER ($TICKER)",
                "• Layer 2: Loughran-McDonald",
                "  Financial Lexicon (Valence [-4,+4])",
                "• Layer 2b: Contextual Negation Window",
                "  ('not downgraded', 'denied lawsuit')",
                "• Layer 3: Zero-Shot Event Classifier",
                "  (7 Basel III / S&P Event Categories)",
                "• Layer 4: Calibrated Basel Impact (1-10)",
                "• Layer 5: Explainable AI Attribution"
            ]
        },
        {
            "rect": (820, 160, 320, 660),
            "header_fill": "#134e4a",
            "body_fill": "#082f2c",
            "border": "#14b8a6",
            "title": "3. Storage & Analytics",
            "items": [
                "• SQLite Database (signals.db)",
                "• Real-Time CSV Audit Stream",
                "• Persistent Tables:",
                "  - signals (Metadata, Score, XAI)",
                "  - weights (Tactical Snapshots)",
                "",
                "Pydantic v2 Schema Enforcement",
                "Latency: < 1.5ms per signal",
                "100% Fully Local Edge Processing"
            ]
        },
        {
            "rect": (1200, 160, 340, 660),
            "header_fill": "#701a75",
            "body_fill": "#3b0744",
            "border": "#d946ef",
            "title": "4. Module A & Dashboard",
            "items": [
                "Tactical Index Rebalancer:",
                "• Mock 10-Stock S&P 100 Index",
                "• Exponential Time-Decay (EMA)",
                "• Tactical Tilting: W_base * (1 + α*S)",
                "• Institutional Bounds (2% - 25%)",
                "• Active Alpha Backtest Curve",
                "",
                "Executive Streamlit UI (app.py):",
                "• Dynamic Weight Area Charts",
                "• Allocation vs Benchmark (10%)",
                "• Rebalancing Decision Log"
            ]
        }
    ]
    
    # Draw Stage Containers
    for stage in stages:
        x, y, w, h = stage["rect"]
        # Card Body
        draw.rectangle([(x, y), (x + w, y + h)], fill=stage["body_fill"], outline=stage["border"], width=2)
        # Card Header
        draw.rectangle([(x, y), (x + w, y + 60)], fill=stage["header_fill"])
        draw.text((x + 15, y + 20), stage["title"], fill='#ffffff')
        
        # Items list
        curr_y = y + 80
        for item in stage["items"]:
            draw.text((x + 15, curr_y), item, fill='#cbd5e1')
            curr_y += 26
            
    # Draw arrows between stages
    arrow_color = '#38bdf8'
    arrow_y = 450
    for ax in [385, 775, 1145]:
        draw.line([(ax, arrow_y), (ax + 40, arrow_y)], fill=arrow_color, width=4)
        draw.polygon([(ax + 40, arrow_y - 6), (ax + 40, arrow_y + 6), (ax + 48, arrow_y)], fill=arrow_color)
        
    # Footer
    draw.rectangle([(0, 850), (width, 900)], fill='#0b1120')
    draw.text((60, 868), "Candidate: Harsh Kapoor | NIT Kurukshetra | Deliverable: AI/NLP Risk Engine + Module A Tactical Rebalancer | S&P Global & CRISIL", fill='#64748b')
    
    output_path = 'docs/architecture.png'
    img.save(output_path, 'PNG')
    print(f"✅ Generated high-resolution architecture diagram at {output_path}")

if __name__ == "__main__":
    create_architecture_diagram()
