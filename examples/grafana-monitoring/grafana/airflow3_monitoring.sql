-- Grafana datasource: PostgreSQL metadata database, using a READ-ONLY role.
-- Tested against the Airflow 3.x metadata model.  These tables are internal
-- Airflow implementation details, so keep this file under version control and
-- revalidate it whenever Airflow is upgraded.
--
-- Grafana variables
--   $Dags (Query, Multi-value, Include All):
--   SELECT DISTINCT dag_id AS __text, dag_id AS __value
--   FROM dag_run ORDER BY 1;
--
-- Use ${Dags:sqlstring} below.  It safely expands multi-select values such as
-- 'daily_sales','daily_inventory' for PostgreSQL.

-- Panel: status of the most recent run of every selected DAG (Table)
WITH latest_runs AS (
    SELECT DISTINCT ON (dr.dag_id)
        dr.dag_id,
        dr.run_id,
        dr.logical_date,
        dr.start_date AS run_start_date,
        dr.end_date AS run_end_date,
        dr.state AS run_state
    FROM dag_run dr
    WHERE dr.dag_id IN (${Dags:sqlstring})
    ORDER BY dr.dag_id,
             COALESCE(dr.start_date, dr.queued_at, dr.logical_date) DESC,
             dr.run_id DESC
),
task_baseline AS (
    SELECT
        ti.dag_id,
        ti.task_id,
        AVG(ti.duration) AS average_duration_seconds,
        COUNT(*) AS successful_runs
    FROM task_instance ti
    WHERE ti.dag_id IN (${Dags:sqlstring})
      AND ti.state = 'success'
      AND ti.end_date >= now() - interval '60 days'
      AND ti.duration IS NOT NULL
    GROUP BY ti.dag_id, ti.task_id
),
latest_tasks AS (
    SELECT
        lr.dag_id,
        lr.run_id,
        lr.logical_date,
        lr.run_start_date,
        lr.run_end_date,
        lr.run_state,
        ti.task_id,
        ti.map_index,
        ti.state AS task_state,
        ti.start_date AS task_start_date,
        ti.end_date AS task_end_date,
        EXTRACT(EPOCH FROM (COALESCE(ti.end_date, now()) - ti.start_date)) AS last_duration_seconds,
        tb.average_duration_seconds,
        tb.successful_runs
    FROM latest_runs lr
    JOIN task_instance ti
      ON ti.dag_id = lr.dag_id
     AND ti.run_id = lr.run_id
    LEFT JOIN task_baseline tb
      ON tb.dag_id = ti.dag_id
     AND tb.task_id = ti.task_id
),
classified_tasks AS (
    SELECT *,
        CASE
            WHEN task_state = 'running'
             AND last_duration_seconds > 900
             AND last_duration_seconds >= average_duration_seconds * 1.3
             AND successful_runs > 10 THEN 'CRITICAL'
            WHEN task_state = 'running'
             AND last_duration_seconds > 180
             AND last_duration_seconds >= average_duration_seconds * 1.3
             AND successful_runs > 10 THEN 'WARNING'
            ELSE 'OK'
        END AS duration_status
    FROM latest_tasks
)
SELECT
    dag_id AS "DAG",
    run_id AS "Run ID",
    logical_date AS "Logical date",
    run_start_date AS "Started at",
    run_end_date AS "Finished at",
    run_state AS "Run state",
    COUNT(*) AS "Tasks",
    COUNT(*) FILTER (WHERE task_state = 'running') AS "Running",
    COUNT(*) FILTER (WHERE task_state = 'success') AS "Success",
    COUNT(*) FILTER (WHERE task_state = 'failed') AS "Failed",
    COUNT(*) FILTER (WHERE task_state NOT IN ('success', 'failed', 'running')) AS "Other",
    COUNT(*) FILTER (WHERE duration_status = 'WARNING') AS "Slow warning",
    COUNT(*) FILTER (WHERE duration_status = 'CRITICAL') AS "Slow critical",
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE task_state IN ('success', 'skipped'))
        / NULLIF(COUNT(*), 0),
        1
    ) AS "Completion %"
FROM classified_tasks
GROUP BY dag_id, run_id, logical_date, run_start_date, run_end_date, run_state
ORDER BY run_start_date DESC NULLS LAST;

-- Panel: selected DAG run durations (Time series; unit = seconds)
SELECT
    COALESCE(dr.start_date, dr.logical_date) AS "time",
    dr.dag_id AS metric,
    EXTRACT(EPOCH FROM (COALESCE(dr.end_date, now()) - dr.start_date)) AS value
FROM dag_run dr
WHERE dr.dag_id IN (${Dags:sqlstring})
  AND dr.start_date IS NOT NULL
  AND $__timeFilter(COALESCE(dr.start_date, dr.logical_date))
ORDER BY 1;

-- Panel: task duration by task (Time series; add $Tasks as a multi-value
-- Grafana variable with: SELECT DISTINCT task_id FROM task_instance ORDER BY 1)
SELECT
    ti.end_date AS "time",
    ti.dag_id || ' / ' || ti.task_id AS metric,
    ti.duration AS value
FROM task_instance ti
WHERE ti.dag_id IN (${Dags:sqlstring})
  AND ti.task_id IN (${Tasks:sqlstring})
  AND ti.state = 'success'
  AND ti.end_date IS NOT NULL
  AND $__timeFilter(ti.end_date)
ORDER BY 1;

-- Panel: failed tasks (Table).  Use the DAG and Run ID columns as a Grafana
-- data link to your own Airflow 3 deployment rather than parsing a timestamp
-- from run_id as the old query did.
SELECT
    dr.dag_id AS "DAG",
    dr.run_id AS "Run ID",
    dr.logical_date AS "Logical date",
    ti.task_id AS "Task",
    ti.map_index AS "Map index",
    ti.try_number AS "Try",
    ti.start_date AS "Started at",
    ti.end_date AS "Finished at",
    ti.state AS "State"
FROM dag_run dr
JOIN task_instance ti
  ON ti.dag_id = dr.dag_id
 AND ti.run_id = dr.run_id
WHERE dr.dag_id IN (${Dags:sqlstring})
  AND ti.state IN ('failed', 'upstream_failed')
  AND $__timeFilter(COALESCE(ti.end_date, ti.start_date, dr.logical_date))
ORDER BY COALESCE(ti.end_date, ti.start_date, dr.logical_date) DESC;

