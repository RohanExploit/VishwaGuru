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

            content_tokens = self._tokenize(content)

            self._prepared_policies.append({
                'title_tokens': self._tokenize(title),
                'content_tokens': content_tokens,
                # Optimization: Pre-calculate token count to avoid repeated len() calls in the hot path
                'token_count': len(content_tokens),
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

        Optimized:
        1. Uses isdisjoint() for fast O(K) early exit where K is min(len(query), len(policy)).
        2. Calculates union length using mathematical formula |A| + |B| - |A ∩ B| in O(1).
        3. Avoids heavy O(N) memory allocation and population of a new union set.
        """
        if not query or not self._prepared_policies:
            return None

        query_tokens = self._tokenize(query)
        len_query = len(query_tokens)
        if not len_query:
            return None

        query_len = len(query_tokens)
        best_score = 0.0
        best_formatted = None

        for prepared in self._prepared_policies:
            policy_tokens = prepared['content_tokens']

            # Optimization 1: Fast early-exit for zero overlap
            if query_tokens.isdisjoint(policy_tokens):
                continue

            # Jaccard Similarity
            # Optimization 2: Calculate intersection using fast bitwise operator
            intersection_len = len(query_tokens & policy_tokens)

            # Optimization 3: Calculate union length mathematically (O(1))
            # |A union B| = |A| + |B| - |A intersect B|
            # This avoids the expensive O(N) set creation of query_tokens.union(policy_tokens)
            union_len = len_query + prepared['token_count'] - intersection_len

            if union_len == 0:
                continue

            score = intersection_len / union_len

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
