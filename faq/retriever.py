import numpy as np
from sentence_transformers import SentenceTransformer

from .models import FAQ


class FAQRetriever:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.faqs = []
        self.embeddings = None
        self.refresh_faqs()

    def refresh_faqs(self):
        print("Fetching FAQs from DB...")
        queryset = FAQ.objects.all().order_by("-created_at")
        self.faqs = list(queryset.values("id", "question", "answer"))
        print(f"Loaded {len(self.faqs)} FAQs.")
        self.embeddings = self.model.encode([f["question"] for f in self.faqs], normalize_embeddings=True)

    def get_best_answer(self, user_question, top_k=1, min_score=0.5):
        user_emb = self.model.encode([user_question], normalize_embeddings=True)[0]
        scores = np.dot(self.embeddings, user_emb)
        best_idx = np.argmax(scores)
        best_score = scores[best_idx]
        if best_score < min_score:
            return None, best_score
        return self.faqs[best_idx]["answer"], best_score
