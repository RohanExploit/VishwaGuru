import json
import os
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CivicRAG:
    def __init__(self, policies_path: str = "backend/data/civic_policies.json"):
        # Performance Boost: Pre-compile regex for faster tokenization
        self._token_regex = re.compile(r'[^a-z0-9\s]')

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
        self.pretokenized_policies = []

        try:
            if os.path.exists(policies_path):
                with open(policies_path, 'r') as f:
                    self.policies = json.load(f)
                logger.info(f"Loaded {len(self.policies)} civic policies for RAG.")

                # Performance Boost: Pre-tokenize all policies during initialization
                # to avoid redundant O(N) processing on every retrieve call.
                for policy in self.policies:
                    content = f"{policy.get('title', '')} {policy.get('text', '')}"
                    self.pretokenized_policies.append({
                        "content_tokens": self._tokenize(content),
                        "title_tokens": self._tokenize(policy.get('title', ''))
                    })
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
                'content_tokens_len': len(content_tokens),
                'formatted': f"**{title}**: {text} (Source: {source})",
                'original': policy
            })

    def _tokenize(self, text: str) -> set:
        """Simple tokenizer: lowercase, remove non-alphanumeric, split."""
        text = text.lower()
        # Performance Boost: Use pre-compiled regex
        text = self._token_regex.sub('', text)
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

        query_tokens_len = len(query_tokens)
        best_score = 0.0
        best_formatted = None

        for policy, pretokenized in zip(self.policies, self.pretokenized_policies):
            # Performance Boost: Use pre-calculated token sets
            policy_tokens = pretokenized["content_tokens"]

            # Optimization: Use isdisjoint() for fast early exit
            if query_tokens.isdisjoint(policy_tokens):
                continue

            # Jaccard Similarity
            # Optimized: Calculate intersection and mathematically deduce union length
            # to avoid creating a new set object in memory for union operations.
            intersection_len = len(query_tokens.intersection(policy_tokens))

            if intersection_len == 0:
                continue

            union_len = len(query_tokens) + len(policy_tokens) - intersection_len
            score = intersection_len / union_len

            # Boost score if title words match (weighted)
            title_tokens = pretokenized["title_tokens"]
            title_match = len(query_tokens.intersection(title_tokens))
            if title_match > 0:
                score += 0.2  # Bonus for title match

            if score > best_score:
                best_score = score
                best_formatted = prepared['formatted']

        if best_score >= threshold and best_formatted:
            return best_formatted

        return None

# Singleton instance
rag_service = CivicRAG()
