import os
import http.client
import json
from langchain.chat_models import ChatOpenAI
from src.agents.agent import Agent
import re

class ExternalAgent(Agent):
    def __init__(self):
        super().__init__()

        # Load API keys
        with open("open_ai_api_key.txt", "r") as file:
            self.openai_api_key = file.read().strip()

        with open("serp_api_key.txt", "r") as file:
            self.serp_api_key = file.read().strip()

        os.environ["OPENAI_API_KEY"] = self.openai_api_key

        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=self.openai_api_key)

    def extract_questions(self, questions_text):
        pattern = r"Question \d+:\s*(.+)"
        return re.findall(pattern, questions_text)

    def analyze_news_article(self, article):
        # Step 1: Generate 5 factual questions
        prompt = (f"You are examining a piece of article that is potentially fake. Suppose you can conduct an internet search, based on the following news text, posit 2 search text surrounding the text you would ask to validate the truthfulness of the article:\n{article['text']}\n"
                 f"Directly answer with Question 1: ... Question 2:...")

        questions = self.llm.predict(prompt)

        questions = self.extract_questions(questions)

        headers = {
            'X-API-KEY': self.serp_api_key,
            'Content-Type': 'application/json'
        }

        conn = http.client.HTTPSConnection("google.serper.dev")
        max_snippets = 20
        results = {}

        for i, question in enumerate(questions):
            print(f"\n🔍 Querying Serper for Question {i+1}: {question}")
            conn.request("POST", "/search", json.dumps({"q": question}), headers)
            res = conn.getresponse()
            search_data = json.loads(res.read().decode("utf-8"))
            snippets = [r.get("snippet") for r in search_data.get("organic", []) if r.get("snippet")]
            results[question] = {
                "raw": search_data,
                "snippets": "\n\n".join(snippets[:max_snippets])
            }

        # Combine all snippets into one for validation
        all_snippets = "\n\n".join(r["snippets"][:max_snippets] for r in results.values())
        print(all_snippets)
        # Step 4: Ask LLM to validate the article
        validation_prompt = (
            f"You are an expert news analyst. Here is a news article excerpt:\n\n"
            f"{article['text']}\n\n"
            f"Here are search results from external sources:\n\n"
            f"{all_snippets}\n\n"
            f"If any external information contradict the article, respond with No. Otherwise, respond with Yes."
            f"If the search result does not provide any information, respond with Yes."
            f"Provide a thorough analysis, followed by a yes or a no."
        )
        validation_result = self.llm.predict(validation_prompt)

        """     
        # Step 5: Save to long-term memory
        self.remember_long_term(article.get("url", "unknown_url"), {
            "questions": questions,
            "search_results": results,
            "validation_result": validation_result
        }) """

        print(validation_result)
        return {
            "generated_question": questions,
            "search_results": results,
            "validation_result": validation_result
        }
