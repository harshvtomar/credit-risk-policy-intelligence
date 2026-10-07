from common import *
sql='\n'.join(line for line in (ROOT/'sql/analysis.sql').read_text().splitlines() if not line.lstrip().startswith('--'))
statements=sql.split(';')
with sqlite3.connect(DATA/'analytics.sqlite') as db:
    for i,statement in enumerate(statements,1):
        if statement.strip():
            result=pd.read_sql_query(statement,db)
            save_table(result,f'sql_result_{i}')
            print(f'Query {i}: {len(result)} rows')
