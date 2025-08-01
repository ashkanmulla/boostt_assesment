-- DDL for main tables
CREATE OR REPLACE TABLE `boostt.analytics.customer_daily` (
    customer_id STRING NOT NULL,
    date DATE NOT NULL,
    geo STRING NOT NULL,
    spend FLOAT64,
    treatment BOOL,
    experiment_id STRING,
    factor_a BOOL,
    factor_b BOOL,
    factor_c BOOL,
    factor_d BOOL,
    factor_e BOOL,
    factor_f BOOL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY date
CLUSTER BY customer_id, experiment_id;

CREATE OR REPLACE TABLE `boostt.analytics.cuped_theta` (
    experiment_id STRING NOT NULL,
    metric STRING NOT NULL,
    theta FLOAT64 NOT NULL,
    standard_error FLOAT64,
    r_squared FLOAT64,
    sample_size INT64,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (experiment_id, metric)
);

CREATE OR REPLACE TABLE `boostt.analytics.experiments_lift` (
    experiment_id STRING NOT NULL,
    metric STRING NOT NULL,
    lift_percentage FLOAT64 NOT NULL,
    confidence_interval_lower FLOAT64,
    confidence_interval_upper FLOAT64,
    p_value FLOAT64,
    is_significant BOOL,
    analysis_type STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (experiment_id, metric, analysis_type)
);

-- Query 1: Update customer_daily table from raw events
CREATE OR REPLACE VIEW `boostt.scheduled_queries.update_customer_daily` AS
WITH daily_data AS (
    SELECT
        customer_id,
        DATE(timestamp) AS date,
        geo,
        SUM(spend) AS spend,
        MAX(CASE WHEN experiment_id IS NOT NULL THEN TRUE ELSE FALSE END) AS in_experiment,
        FIRST_VALUE(experiment_id IGNORE NULLS) OVER (
            PARTITION BY customer_id, DATE(timestamp) 
            ORDER BY timestamp DESC
        ) AS experiment_id,
        -- Extract treatment and factors similarly
        FIRST_VALUE(treatment IGNORE NULLS) OVER (
            PARTITION BY customer_id, DATE(timestamp) 
            ORDER BY timestamp DESC
        ) AS treatment,
        -- Add other factors here...
        FIRST_VALUE(factor_a IGNORE NULLS) OVER (
            PARTITION BY customer_id, DATE(timestamp)
            ORDER BY timestamp DESC
        ) AS factor_a,
        FIRST_VALUE(factor_b IGNORE NULLS) OVER (
            PARTITION BY customer_id, DATE(timestamp)
            ORDER BY timestamp DESC
        ) AS factor_b
    FROM `boostt.raw_data.events`
    WHERE DATE(timestamp) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    GROUP BY customer_id, date, geo
)
SELECT
    customer_id, date, geo, spend, treatment, experiment_id,
    factor_a, factor_b, 
    -- Add other factors as needed
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM daily_data
WHERE in_experiment = TRUE OR spend > 0;

-- Query 2: Calculate CUPED theta 
CREATE OR REPLACE VIEW `boostt.scheduled_queries.calculate_cuped_theta` AS
WITH experiment_data AS (
    -- Get pre/post spend for each customer in each experiment
    SELECT
        e.experiment_id,
        cd.customer_id,
        cd.treatment,
        AVG(CASE WHEN cd.date < e.start_date THEN cd.spend ELSE NULL END) AS pre_spend,
        AVG(CASE WHEN cd.date BETWEEN e.start_date AND e.end_date THEN cd.spend ELSE NULL END) AS post_spend
    FROM `boostt.analytics.customer_daily` cd
    JOIN `boostt.analytics.experiments` e ON cd.experiment_id = e.experiment_id
    WHERE e.status = 'ACTIVE' AND e.analysis_date = CURRENT_DATE()
    GROUP BY 1, 2, 3
),
control_data AS (
    -- Filter to just control group with valid pre/post data
    SELECT * FROM experiment_data
    WHERE treatment = FALSE AND pre_spend IS NOT NULL AND post_spend IS NOT NULL
)
-- Calculate theta for each experiment
SELECT
    experiment_id,
    'spend' AS metric,
    -- OLS formula for theta: Cov(pre, post) / Var(pre)
    SAFE_DIVIDE(
        SUM((pre_spend - AVG(pre_spend)) * (post_spend - AVG(post_spend))),
        SUM(POW(pre_spend - AVG(pre_spend), 2))
    ) AS theta,
    -- Also calculate standard error, R², etc.
    -- [additional calculations]
    COUNT(*) AS sample_size,
    CURRENT_TIMESTAMP() AS created_at
FROM control_data
GROUP BY experiment_id;

-- Query 3: Calculate experiment lift with CUPED
CREATE OR REPLACE VIEW `boostt.scheduled_queries.calculate_experiments_lift` AS
WITH experiment_data AS (
    -- Similar to above, get pre/post data
    -- [simplified for brevity]
),
adjusted_metrics AS (
    -- Apply CUPED adjustment
    SELECT
        ed.experiment_id,
        ed.customer_id,
        ed.treatment,
        ed.post_spend,
        -- CUPED formula: Y - theta * (X - X̄)
        ed.post_spend - COALESCE(tv.theta, 0) * (ed.pre_spend - AVG(ed.pre_spend) OVER (PARTITION BY ed.experiment_id)) AS adjusted_post_spend
    FROM experiment_data ed
    LEFT JOIN `boostt.analytics.cuped_theta` tv 
    ON ed.experiment_id = tv.experiment_id AND tv.metric = 'spend'
)
-- Calculate and output final lift metrics
SELECT
    experiment_id,
    'spend' AS metric,
    -- Calculate lift percentage
    100 * SAFE_DIVIDE(cuped_treatment_effect, control_mean) AS lift_percentage,
    -- Calculate confidence intervals
    -- [calculations for CI]
    -- Calculate p-value
    -- [p-value calculation]
    'CUPED' AS analysis_type,
    CURRENT_TIMESTAMP() AS created_at
FROM experiment_stats;