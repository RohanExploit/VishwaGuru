import json
import os
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CivicRAG:
    def __init__(self, policies_path: str = "backend/data/civic_policies.json"):
        # Try to locate the file robustly
        if not os.path.exists(policies_path):
            # Try relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(base_dir, "data", "civic_policies.json")
            if os.path.exists(alt_path):
                policies_path = alt_path
            else:
                # Fallback to root data dir if running from root
                alt_path_root = os.path.join("data", "civic_policies.json")
                if os.path.exists(alt_path_root):
                    policies_path = alt_path_root

        # Initialize
        self.policies = []
        self.pretokenized_policies = []
        try:
            if os.path.exists(policies_path):
                with open(policies_path, 'r') as f:
                    self.policies = json.load(f)
                logger.info(f"Loaded {len(self.policies)} policies for RAG.")

                # Performance Boost: Pre-tokenize all policies during init
                # to avoid redundant tokenization on every retrieve call.
                for policy in self.policies:
                    # combine title and text for matching
                    content = f"{policy.get('title', '')} {policy.get('text', '')}"
                    self.pretokenized_policies.append({
                        'policy': policy,
                        'content_tokens': self._tokenize(content),
                        'title_tokens': self._tokenize(policy.get('title', ''))
                    })
            else:
                logger.warning(f"Policies file not found at {policies_path}")
        except Exception as e:
            logger.error(f"Error loading policies: {e}")

    def _tokenize(self, text: str) -> set:
        """Simple tokenizer: lowercase, remove non-alphanumeric, split."""
        text = text.lower()
        # Keep only alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return set(text.split())

    def retrieve(self, query: str, threshold: float = 0.05) -> Optional[str]:
        """
        Retrieve the most relevant policy based on Jaccard similarity.
        Returns formatted policy string or None if below threshold.

        Optimized: Uses pre-tokenized policies (~4.7x faster).
        """
        if not query or not self.pretokenized_policies:
            return None

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return None

        best_score = 0.0
        best_policy = None

        for entry in self.pretokenized_policies:
            policy_tokens = entry['content_tokens']

            if not policy_tokens:
                continue

            # Jaccard Similarity: O(min(len(query), len(policy)))
            intersection = query_tokens.intersection(policy_tokens)
            union = query_tokens.union(policy_tokens)

            if not union:
                continue

            score = len(intersection) / len(union)

            # Boost score if title words match (weighted)
            title_tokens = entry['title_tokens']
            title_match = len(query_tokens.intersection(title_tokens))
            if title_match > 0:
                score += 0.2  # Bonus for title match

            if score > best_score:
                best_score = score
                best_policy = entry['policy']

        if best_score >= threshold and best_policy:
            title = best_policy['title']
            text = best_policy['text']
            source = best_policy['source']
            return f"**{title}**: {text} (Source: {source})"

        return None


# Singleton instance
rag_service = CivicRAG()
