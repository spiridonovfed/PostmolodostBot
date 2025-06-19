from sentence_transformers import SentenceTransformer

from content.models import Topic


class TopicRetriever:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.topics = []
        self.embeddings = None
        self.refresh_topics_from_db()

    def refresh_topics_from_db(self):
        print("Fetching topics from DB...")
        queryset = Topic.objects.all().order_by("title")
        self.topics = list(queryset.values("id", "title", "text"))
        print(f"Loaded {len(self.topics)} topics.")
        self.embeddings = self.model.encode([f["title"] for f in self.topics], normalize_embeddings=True)
