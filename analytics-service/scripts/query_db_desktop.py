import sqlite3
p = r'C:/Users/Sahil Belchada/Desktop/marketmind.db'
conn = sqlite3.connect(p)
c = conn.cursor()

print('DB file:', p)
print('Tables:')
for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"): 
    print(' -', r[0])

# counts
for t in ['fact_agent_evaluation','fact_agent_retrieval']:
    try:
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception as e:
        cnt = f'ERR: {e}'
    print(f"{t}: {cnt}")

print('\nSample evaluations (first 10):')
try:
    rows = c.execute('SELECT eval_id, question_id, predicted_answer, ground_truth, correct_at_1, correct_at_5, faithfulness_score, hallucinated, latency_ms, created_at FROM fact_agent_evaluation ORDER BY eval_id DESC LIMIT 10').fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('Unable to query fact_agent_evaluation:', e)

# For each sample eval, show retrievals
if rows:
    for r in rows:
        eval_id = r[0]
        print(f"\nRetrievals for eval_id={eval_id}:")
        try:
            rets = c.execute(f"SELECT retrieval_id, rank, doc_id, is_relevant, similarity_score FROM fact_agent_retrieval WHERE eval_id=? ORDER BY rank ASC LIMIT 10", (eval_id,)).fetchall()
            if rets:
                for rr in rets:
                    print('  ', rr)
            else:
                print('  No retrieval rows for this eval')
        except Exception as e:
            print('  Error querying retrievals:', e)

conn.close()
