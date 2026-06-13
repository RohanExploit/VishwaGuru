import json
import os
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CivicRAG:
    def __init__(self, policies_path: str = "backend/data/civic_policies.json"):
        # Pre-compile regex for performance
        self._tokenizer_re = re.compile(r'[^a-z0-9\s]')

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

        self.policies = []
        self._prepared_policies = []
        try:
            if os.path.exists(policies_path):
                with open(policies_path, 'r') as f:
                    self.policies = json.load(f)
                self._prepare_policies()
                logger.info(f"Loaded and prepared {len(self.policies)} civic policies for RAG.")
            else:
                logger.warning(f"Civic policies file not found at {policies_path}")
        except Exception as e:
            logger.error(f"Error loading policies: {e}")

    def _prepare_policies(self):
        """Pre-tokenize and pre-format policies for faster retrieval."""
        self._prepared_policies = []
        for policy in self.policies:
            title = policy.get('title', '')
            text = policy.get('text', '')
            source = policy.get('source', 'Unknown')

            content = f"{title} {text}"
            content_tokens = self._tokenize(content)

            self._prepared_policies.append({
                'title_tokens': self._tokenize(title),
                'content_tokens': content_tokens,
                'content_token_count': len(content_tokens),
                'formatted': f"**{title}**: {text} (Source: {source})",
                'original': policy
            })

    def _tokenize(self, text: str) -> set:
        """Simple tokenizer: lowercase, remove non-alphanumeric, split."""
        text = text.lower()
        # Keep only alphanumeric and spaces - using pre-compiled regex
        text = self._tokenizer_re.sub('', text)
        return set(text.split())

    def retrieve(self, query: str, threshold: float = 0.05) -> Optional[str]:
        """
        Retrieve the most relevant policy based on Jaccard similarity of tokens.
        Returns the formatted policy string or None if below threshold.
        Optimized: Uses pre-calculated token lengths and mathematical union to avoid O(N) union.
        """
        if not query or not self._prepared_policies:
            return None

        query_tokens = self._tokenize(query)
        query_token_count = len(query_tokens)
        if query_token_count == 0:
            return None

        query_len = len(query_tokens)
        best_score = 0.0
        best_formatted = None

        for prepared in self._prepared_policies:
            policy_tokens = prepared['content_tokens']

            # Performance: Use isdisjoint for fast early-exit when there is no overlap
            if query_tokens.isdisjoint(policy_tokens):
                continue

            # Jaccard Similarity: |A ∩ B| / |A ∪ B|
            intersection_count = len(query_tokens.intersection(policy_tokens))

            # Performance: Use mathematical formula for union length: |A ∪ B| = |A| + |B| - |A ∩ B|
            # This avoids O(N) allocation and population of a new union set.
            union_count = query_token_count + prepared['content_token_count'] - intersection_count

            if union_count == 0:
                continue

            score = intersection_count / union_count

            # Boost score if title words match (weighted)
            title_tokens = prepared['title_tokens']
            if not query_tokens.isdisjoint(title_tokens):
                score += 0.2  # Bonus for title match

            if score > best_score:
                best_score = score
                best_formatted = prepared['formatted']

        if best_score >= threshold and best_formatted:
            return best_formatted

        return None

# Singleton instance
rag_service = CivicRAG()
