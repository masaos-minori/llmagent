-- ──────────────────────────────────────────────────────────────────────────
-- rrf.sql
-- agent.py の各検索関数が実行する SQL の参照定義
-- ──────────────────────────────────────────────────────────────────────────

-- ──────────────────────────────────────────────────────────────────────────
-- 1. ベクトル検索 (KNN: K Nearest Neighbors)
-- ──────────────────────────────────────────────────────────────────────────
-- パラメータ:
--   ?1 : float32 リトルエンディアン BLOB (384 次元クエリベクトル)
--   ?2 : 取得件数 (top_k)
--
-- chunks_vec.distance は L2 距離。値が小さいほど意味的に近い。
-- sqlite-vec の MATCH 演算子でベクトル最近傍検索を行う。
SELECT c.chunk_id,
       c.content,
       d.url,
       d.title,
       cv.distance
FROM   chunks_vec cv
JOIN   chunks     c  ON c.chunk_id = cv.chunk_id
JOIN   documents  d  ON d.doc_id   = c.doc_id
WHERE  cv.embedding MATCH ?1
ORDER  BY cv.distance
LIMIT  ?2;


-- ──────────────────────────────────────────────────────────────────────────
-- 2. 全文検索 (BM25: Best Matching 25)
-- ──────────────────────────────────────────────────────────────────────────
-- パラメータ:
--   ?1 : FTS5 クエリ文字列 (各トークンをダブルクォートで囲んだ形式推奨)
--   ?2 : 取得件数 (top_k)
--
-- bm25() の返り値は負値。値が小さいほど高関連度。
-- BM25 は TF-IDF を改良した確率的ランキング関数で、語の出現頻度と
-- ドキュメント長を考慮したスコアを算出する。
SELECT c.chunk_id,
       c.content,
       d.url,
       d.title,
       bm25(chunks_fts) AS bm25_score
FROM   chunks_fts
JOIN   chunks     c  ON c.chunk_id = chunks_fts.rowid
JOIN   documents  d  ON d.doc_id   = c.doc_id
WHERE  chunks_fts MATCH ?1
ORDER  BY bm25(chunks_fts)
LIMIT  ?2;


-- ──────────────────────────────────────────────────────────────────────────
-- 3. RRF 融合 (Python 側で実装)
-- ──────────────────────────────────────────────────────────────────────────
-- RRF (Reciprocal Rank Fusion: 相互順位融合) の計算式:
--   score(d) = Σ_i  1 / (k + rank_i(d))
--     k      : 定数 (標準値 60)。ランク下位の影響を緩和する。
--     rank_i : i 番目の検索結果リストにおけるドキュメント d の順位 (1 始まり)
--
-- SQLite では異なる結果セットのランクをまたいだ集計が困難なため、
-- Python の rrf_merge() 関数で実装する (agent.py 参照)。
