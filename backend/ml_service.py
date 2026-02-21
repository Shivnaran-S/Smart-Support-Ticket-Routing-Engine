# backend/ml_service.py
import time
import re
from sentence_transformers import SentenceTransformer, util

class TicketRouterML:
    def __init__(self):
        # Lazy loading for heavy models to save memory during init
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.history = [] # In-memory list for recent ticket embeddings (time-windowed in production)

    def baseline_classify(self, text: str) -> tuple[str, float]:
        """Milestone 1: Baseline heuristics"""
        text_lower = text.lower()
        if "bill" in text_lower or "invoice" in text_lower:
            category = "Billing"
        elif "legal" in text_lower or "law" in text_lower:
            category = "Legal"
        else:
            category = "Technical"
        
        urgency = 1.0 if re.search(r'\b(broken|asap|urgent)\b', text_lower) else 0.0
        return category, urgency

    def transformer_classify(self, text: str) -> tuple[str, float]:
        """Milestone 2: Deep Learning approach"""
        start_time = time.time()
        
        # Simulate Transformer inference (replace with actual HuggingFace pipeline)
        time.sleep(0.1) # Simulating latency
        category = "Technical" # Mock classification
        urgency_score = 0.85 # Mock S in [0,1]
        
        if (time.time() - start_time) > 0.5:
            # Circuit Breaker: Latency > 500ms
            raise TimeoutError("Transformer latency exceeded 500ms")
            
        return category, urgency_score

    def process_ticket(self, text: str) -> tuple[str, float]:
        """Orchestrates the circuit breaker"""
        try:
            return self.transformer_classify(text)
        except TimeoutError:
            return self.baseline_classify(text)

    def check_storm(self, text: str) -> bool:
        """Milestone 3: Semantic deduplication"""
        new_emb = self.encoder.encode(text, convert_to_tensor=True)
        similar_count = 0
        
        for hist_text, hist_emb in self.history[-50:]: # Check recent 50
            similarity = util.cos_sim(new_emb, hist_emb).item()
            if similarity > 0.9:
                similar_count += 1
                
        self.history.append((text, new_emb))
        
        # If > 10 similar tickets, trigger Master Incident logic
        return similar_count >= 10