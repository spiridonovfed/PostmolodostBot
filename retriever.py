from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from content.models import Topic


class TopicRetriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.topics = []
        self.embeddings = None
        self.refresh_topics_from_db()

    def refresh_topics_from_db(self):
        print("Fetching topics from DB...")
        queryset = Topic.objects.all().order_by("title")
        self.topics = list(queryset.values("id", "title", "text"))
        print(f"Loaded {len(self.topics)} topics.")

        corpus = [f"{t['title']} {t['text']}" for t in self.topics]
        self.embeddings = self.vectorizer.fit_transform(corpus)

    def query(self, user_input, top_k=4):
        user_emb = self.vectorizer.transform([user_input])
        scores = cosine_similarity(self.embeddings, user_emb).flatten()
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            self.topics[i] for i in top_indices if scores[i] > 0.1
        ]  # tune threshold as needed
