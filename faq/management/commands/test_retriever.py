from django.core.management.base import BaseCommand

from faq.retriever import FAQRetriever


class Command(BaseCommand):
    help = "Test semantic FAQ retriever interactively."

    def handle(self, *args, **kwargs):
        retriever = FAQRetriever()
        while True:
            q = input("Ask a question (or blank to exit): ")
            if not q.strip():
                break
            answer, score = retriever.get_best_answer(q)
            if answer:
                print(f"Best answer (score {score:.2f}): {answer}")
            else:
                print("No relevant answer found.")
