FROM apache/airflow:3.3.0

# Airflow is supplied by the base image; --no-deps keeps pip from replacing the
# image's tested Airflow dependency set. Install this checkout so the example
# exercises the code under development instead of a published package.
COPY pyproject.toml README.md ./
COPY airflow_embedash ./airflow_embedash
RUN pip install --no-cache-dir --no-deps .
