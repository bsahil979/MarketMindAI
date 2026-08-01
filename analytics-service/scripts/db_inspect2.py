import sqlite3
p = r'C:/Users/Sahil Belchada/Desktop/maybe the final year project/marketmind.db'
conn = sqlite3.connect(p)
c = conn.cursor()
print('tables:', [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table';")])
for t in ['fact_agent_evaluation','fact_agent_retrieval']:
    try:
        print(t, c.execute(f'SELECT count(*) FROM {t}').fetchone()[0])
    except Exception as e:
        print(t, 'ERR', e)
conn.close()
