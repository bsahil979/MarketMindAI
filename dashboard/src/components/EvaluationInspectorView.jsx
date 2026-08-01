import React from 'react';

export default function EvaluationInspectorView({
  inspectorEvalId,
  setInspectorEvalId,
  loadInspection,
  inspectorLoading,
  inspectorError,
  inspectorEval,
  inspectorRetrievals,
  setInspectorEval,
  setInspectorRetrievals,
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <input
          type="text"
          className="input-field"
          placeholder="Evaluation ID (e.g. 1 or bench_0001)"
          value={inspectorEvalId}
          onChange={(e) => setInspectorEvalId(e.target.value)}
          style={{ flex: 1 }}
        />
        <button onClick={() => loadInspection(inspectorEvalId)} className="btn btn-primary">Load</button>
        <button onClick={() => { setInspectorEvalId(''); setInspectorEval(null); setInspectorRetrievals([]); }} className="btn">Clear</button>
      </div>

      {inspectorLoading && (
        <div className="glass-panel" style={{ padding: '20px', textAlign: 'center' }}><div className="spinner"></div></div>
      )}

      {inspectorError && (
        <div className="glass-panel" style={{ padding: '16px', color: '#f87171' }}>{inspectorError}</div>
      )}

      {inspectorEval && (
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ marginTop: 0 }}>Evaluation #{inspectorEval.eval_id}</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div><strong>Question ID:</strong> {inspectorEval.question_id}</div>
            <div><strong>Latency (ms):</strong> {inspectorEval.latency_ms}</div>
            <div style={{ gridColumn: '1 / -1' }}><strong>Question:</strong> <div style={{ color: '#cbd5e1' }}>{inspectorEval.question || ''}</div></div>
            <div style={{ gridColumn: '1 / -1' }}><strong>Predicted Answer:</strong> <div style={{ color: '#f8fafc' }}>{inspectorEval.predicted_answer}</div></div>
            <div style={{ gridColumn: '1 / -1' }}><strong>Ground Truth:</strong> <div style={{ color: '#94a3b8' }}>{inspectorEval.ground_truth}</div></div>
            <div><strong>Correct@1:</strong> {inspectorEval.correct_at_1}</div>
            <div><strong>Correct@5:</strong> {inspectorEval.correct_at_5}</div>
            <div><strong>Faithfulness:</strong> {inspectorEval.faithfulness_score}</div>
            <div><strong>Hallucinated:</strong> {inspectorEval.hallucinated}</div>
            <div><strong>Semantic Similarity:</strong> {inspectorEval.semantic_similarity?.toFixed ? inspectorEval.semantic_similarity.toFixed(3) : inspectorEval.semantic_similarity}</div>
          </div>
        </div>
      )}

      {inspectorRetrievals && inspectorRetrievals.length > 0 && (
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h4 style={{ marginTop: 0 }}>Retrieval Candidates (ordered by rank)</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)' }}>
                  <th style={{ padding: '10px' }}>Rank</th>
                  <th style={{ padding: '10px' }}>Doc ID</th>
                  <th style={{ padding: '10px' }}>Similarity</th>
                  <th style={{ padding: '10px' }}>Is Relevant</th>
                  <th style={{ padding: '10px' }}>Snippet</th>
                </tr>
              </thead>
              <tbody>
                {inspectorRetrievals.map(r => (
                  <tr key={r.retrieval_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '10px', fontWeight: '700' }}>{r.rank}</td>
                    <td style={{ padding: '10px' }}>{r.doc_id}</td>
                    <td style={{ padding: '10px' }}>{r.similarity_score != null ? (r.similarity_score.toFixed ? r.similarity_score.toFixed(3) : r.similarity_score) : 'n/a'}</td>
                    <td style={{ padding: '10px' }}>{r.is_relevant != null ? (r.is_relevant ? '✅' : '❌') : '—'}</td>
                    <td style={{ padding: '10px' }}>{r.snippet}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
