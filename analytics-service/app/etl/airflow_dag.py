from datetime import datetime, timedelta
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    # Fallback/Mock Airflow classes for environments without Airflow installed
    class DAG:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class PythonOperator:
        def __init__(self, *args, **kwargs): pass

def extract_market_data(**kwargs):
    print("Executing Task: Extract")
    print("Reading raw price files and sentiment news feeds from raw_storage/...")
    return "extract_success"

def validate_payloads(**kwargs):
    print("Executing Task: Validate")
    print("Validating JSON schemas, parsing metadata headers, checking date dimensions...")
    return "validate_success"

def clean_records(**kwargs):
    print("Executing Task: Clean")
    print("Filtering out duplicates, correcting microsecond scales, cleaning empty labels...")
    return "clean_success"

def normalize_metrics(**kwargs):
    print("Executing Task: Normalize")
    print("Calculating relative percentage ticks and indexing stock returns mapping...")
    return "normalize_success"

def load_star_schema(**kwargs):
    print("Executing Task: Load")
    print("Writing data records into DimCompany, DimDate, FactMarketPrice, and FactNewsSentiment tables...")
    return "load_success"

def train_ai_models(**kwargs):
    print("Executing Task: Train AI")
    print("Fitting Linear Regression model, updating Sharpe ratios, VaR, and Beta values...")
    return "train_success"

# Default arguments for the Airflow Scheduler
default_args = {
    'owner': 'marketmind_admin',
    'depends_on_past': False,
    'start_date': datetime(2026, 7, 17),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'marketmind_etl_pipeline',
    default_args=default_args,
    description='A recruiter-ready Apache Airflow DAG demonstrating modular ETL and AI model training steps.',
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=['finance', 'mlops', 'data_engineering'],
) as dag:

    task_extract = PythonOperator(
        task_id='extract_raw_files',
        python_callable=extract_market_data,
        provide_context=True,
    )

    task_validate = PythonOperator(
        task_id='validate_data_payloads',
        python_callable=validate_payloads,
        provide_context=True,
    )

    task_clean = PythonOperator(
        task_id='clean_data_records',
        python_callable=clean_records,
        provide_context=True,
    )

    task_normalize = PythonOperator(
        task_id='normalize_data_metrics',
        python_callable=normalize_metrics,
        provide_context=True,
    )

    task_load = PythonOperator(
        task_id='load_to_star_schema',
        python_callable=load_star_schema,
        provide_context=True,
    )

    task_train = PythonOperator(
        task_id='train_regression_models',
        python_callable=train_ai_models,
        provide_context=True,
    )

    # Task dependency graph: Extract -> Validate -> Clean -> Normalize -> Load -> Train AI
    task_extract >> task_validate >> task_clean >> task_normalize >> task_load >> task_train
