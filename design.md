# Causal Measurement Pipeline - Design Brief

## Overview

This pipeline connects experiment results to Boostt's RL budget optimizer. The key insight: by measuring lift more precisely, we provide better rewards for the RL agent, leading to smarter budget allocation.

## Key Components & Flow

1. **Experiment Design**
   - Fractional factorial designs to test multiple factors efficiently
   - Resolution-IV ensures main effects aren't confounded with 2-factor interactions
   - Designs automatically generated based on factor count

2. **Data Collection & Processing**
   - Raw events flow into BigQuery
   - Daily scheduled queries aggregate to customer_daily
   - Pre/post metrics calculated for each customer

3. **Variance Reduction**
   - CUPED leverages pre-experiment data to reduce noise
   - For geo-experiments, synthetic control creates counterfactuals
   - Both approaches significantly tighten confidence intervals

4. **Lift Calculation**
   - Statistical inference on adjusted metrics
   - Confidence intervals account for variance reduction
   - Results stored in experiments_lift table

5. **RL Integration**
   - Lift metrics converted to Reward messages
   - Vertex AI consumes rewards to train policy
   - Updated policy deployed for budget decisions

## Architecture