
import logging
import hashlib
import struct
import math

logger = logging.getLogger(__name__)


class Embedder:
	"""Lightweight embedder with lazy SentenceTransformer import.

	- Tries to import `sentence_transformers.SentenceTransformer` on first use.
	- If unavailable, falls back to a deterministic hash-based embedding
	  so the rest of the framework can still run (useful for CI or
	  environments where heavy ML deps are not installed).
	"""

	def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
		self._model_name = model_name
		self._model = None
		self._backend = None  # 'st' for sentence-transformers, 'hash' for fallback
		self._initialized = False
		self.cache = {}

	def _init_model(self):
		if self._initialized:
			return
		self._initialized = True
		try:
			from sentence_transformers import SentenceTransformer  # local import

			self._model = SentenceTransformer(self._model_name)
			self._backend = "st"
			logger.info("Loaded SentenceTransformer model: %s", self._model_name)
		except Exception as e:
			# Fall back to cheap deterministic hash-based embedding
			self._model = None
			self._backend = "hash"
			logger.warning(
				"sentence-transformers not available or failed to load (%s). "
				"Falling back to lightweight hash embeddings.",
				e,
			)

	def _hash_embedding(self, text: str, dim: int = 64):
		# Deterministic embedding generated from repeated sha256 digests.
		# Produces `dim` floats in range [-1, 1].
		out = []
		counter = 0
		while len(out) < dim:
			h = hashlib.sha256()
			h.update(text.encode("utf-8"))
			h.update(struct.pack("I", counter))
			digest = h.digest()
			for b in digest:
				if len(out) >= dim:
					break
				# map byte (0..255) to float in [-1,1]
				out.append((b / 255.0) * 2.0 - 1.0)
			counter += 1
		# Normalize to unit length to make cosine similarity sensible
		norm = math.sqrt(sum(x * x for x in out))
		if norm > 0:
			out = [x / norm for x in out]
		return out

	def encode(self, text: str):
		if text in self.cache:
			return self.cache[text]
		self._init_model()
		if self._backend == "st":
			# SentenceTransformer's encode may accept lists; ensure we return 1-D array
			emb = self._model.encode(text)
			self.cache[text] = emb
			return emb
		# fallback
		emb = self._hash_embedding(text, dim=64)
		self.cache[text] = emb
		return emb

