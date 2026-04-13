import json
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from ai_locator.embedder import Embedder

class AILocatorEngine:

    def __init__(self, locator_file="locators.json"):
        # Resolve path: try as-is, then relative to package root, then create empty default
        loc_path = Path(locator_file)
        if not loc_path.is_absolute():
            if not loc_path.exists():
                pkg_root = Path(__file__).resolve().parents[1]
                loc_path = pkg_root / locator_file
        
        # If file still doesn't exist, create an empty array
        if not loc_path.exists():
            print(f"Creating default empty locators file at {loc_path}")
            loc_path.parent.mkdir(parents=True, exist_ok=True)
            with open(loc_path, "w") as f:
                json.dump([], f)
        
        self.locator_file = str(loc_path)
        with open(self.locator_file, "r") as f:
            self.db = json.load(f)
        self.embedder = Embedder()

    def best_match(self, query):
        query_emb = self.embedder.encode(query)

        # Heuristic: for email/password, prefer <input> elements with matching name/type
        lowered_query = query.lower()
        candidates = self.db

        if lowered_query in ["email", "password"]:
            # Only consider <input> elements
            candidates = [item for item in self.db if item["tag"] == "input"]

        best = None
        best_score = -1

        for item in candidates:
            combined = f"{item['tag']} {item['text']} "
            for k, v in item["attributes"].items():
                combined += f"{k} {v} "

            elem_emb = self.embedder.encode(combined)
            score = cosine_similarity([query_emb], [elem_emb])[0][0]

            # Boost score for exact name match
            if lowered_query in ["email", "password"]:
                name = item["attributes"].get("name", "").lower()
                typ = item["attributes"].get("type", "").lower()
                if name == lowered_query or typ == lowered_query:
                    score += 1.0  # Strong boost for exact match

            if score > best_score:
                best_score = score
                best = item

        return best
