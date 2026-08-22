# Distance Metric Comparison — Cosine vs. Euclidean vs. Dot Product

**Checkpoint 2, Deliverable 9.** Full experiment script: `tests/distance_metric_experiment.py`
(reproducible — run `python -m tests.distance_metric_experiment`).

## Method
We vectorized every chunk in the real FitGen dataset (84 chunks from 5
training-principle documents + 52 exercises) using TF-IDF, then ran three
sample queries against all three metrics: cosine similarity, Euclidean
(L2) distance, and raw dot product. TF-IDF was used for this specific
comparison (instead of the dense sentence-transformer embeddings used in
production, see `src/ingest/embed_store.py`) so the experiment runs
offline and deterministically — the *behavior* of each metric generalizes
to any vector space.

## Results

**Query: "beginner 3 day full body workout with dumbbells"**
| Rank | Cosine | Euclidean | Dot Product |
|---|---|---|---|
| 1 | `03_program_design_splits.md::chunk2` (0.1028) | same chunk (1.3395) | same chunk (0.1028) |
| 2 | `exercises.csv#row40` (0.1025) | same chunk (1.3397) | same chunk (0.1025) |
| 3 | `02_warmup_cooldown.md::chunk1` (0.0963) | same chunk (1.3444) | same chunk (0.0963) |

**Query: "my knees hurt during squats, what should I do"**
| Rank | Cosine | Euclidean | Dot Product |
|---|---|---|---|
| 1 | `04_injury_safety_modifications.md::chunk2` (0.3156) | same (1.1699) | same (0.3156) |
| 2 | `exercises.csv#row5` (0.1645) | same (1.2927) | same (0.1645) |
| 3 | `exercises.csv#row8` (0.1463) | same (1.3067) | same (0.1463) |

**Query: "how many sets and reps for building muscle"**
| Rank | Cosine | Euclidean | Dot Product |
|---|---|---|---|
| 1 | `05_reps_sets_rest_guidelines.md::chunk0` (0.2875) | same (1.1937) | same (0.2875) |
| 2 | `05_reps_sets_rest_guidelines.md::chunk1` (0.2871) | same (1.1941) | same (0.2871) |
| 3 | `03_program_design_splits.md::chunk1` (0.2182) | same (1.2504) | same (0.2182) |

## Why all three metrics agree here
`TfidfVectorizer` L2-normalizes every vector by default (`‖v‖ = 1`). For
unit-length vectors, cosine similarity and dot product are mathematically
identical (`cos(a,b) = a·b` when `‖a‖=‖b‖=1`), and Euclidean distance is a
monotonic transform of cosine similarity: `‖a-b‖² = 2 − 2·cos(a,b)`. So on
normalized vectors, all three metrics must produce the same ranking — our
results confirm the math exactly (e.g. rank order is identical in every
query above).

**This is not just a quirk of TF-IDF.** The sentence-transformer embeddings
we use in production (`all-MiniLM-L6-v2`) are also unit-normalized by
convention, so the same equivalence holds for our actual retrieval pipeline.

## When the metrics would actually diverge
- **Unnormalized vectors** (e.g., raw word-count vectors, or embeddings
  from a model that doesn't normalize output): longer/more verbose chunks
  get inflated dot-product and cosine scores unless corrected, while
  Euclidean distance is sensitive to magnitude in a different way. This is
  a common bug source in naive RAG implementations.
- **Dot product without normalization** rewards vector magnitude, which
  can bias retrieval toward longer documents — the exact failure our
  exercise-row chunking (Checkpoint 3) avoids by keeping each exercise as
  one short, atomic chunk.

## Recommendation
**Cosine similarity**, for two reasons specific to this project:
1. It's magnitude-invariant, so a short exercise description and a long
   training-principle paragraph are compared fairly regardless of length.
2. FAISS's `IndexFlatIP` (inner product) index computes dot product
   efficiently — and since our embeddings are pre-normalized, inner
   product *is* cosine similarity, giving us cosine's correctness with
   dot product's speed. This is what `langchain_community.vectorstores.FAISS`
   uses by default with our HuggingFace embeddings.
