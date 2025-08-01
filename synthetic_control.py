import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.preprocessing import StandardScaler

def build_synthetic_control(
    df, 
    target_geo,
    outcome_col,
    time_col,
    geo_col,
    pre_period_end=None,
    method='ridge',
    alpha=None
):
    """
    Build a synthetic control model for geo-locked treatments.
    
    Honestly, this is one of the trickier parts of the assessment.
    The key insight is using control geos to predict outcomes in the treated geo.
    """
    # Input validation
    if method not in ['ridge', 'lasso']:
        raise ValueError("Method must be either 'ridge' or 'lasso'")
    
    # Default pre_period_end to median time if not specified
    if pre_period_end is None:
        pre_period_end = df[time_col].median()
    
    # Split data into pre/post periods
    pre_data = df[df[time_col] <= pre_period_end].copy()
    post_data = df[df[time_col] > pre_period_end].copy()
    
    # Make sure target geo exists
    if target_geo not in pre_data[geo_col].unique():
        raise ValueError(f"Target geo '{target_geo}' not found in data")
    
    # Get control geos (all except target)
    control_geos = pre_data[pre_data[geo_col] != target_geo][geo_col].unique()
    
    # Reshape data for modeling - we need time as rows, geos as columns
    pivot_pre = pre_data.pivot_table(
        index=time_col, 
        columns=geo_col, 
        values=outcome_col,
        aggfunc='mean'
    )
    
    # Prepare features (control geos) and target (target geo)
    X_pre = pivot_pre[control_geos].values
    y_pre = pivot_pre[target_geo].values
    
    # Scale features for better model performance
    scaler = StandardScaler()
    X_pre_scaled = scaler.fit_transform(X_pre)
    
    # Select best alpha via cross-validation if not provided
    if alpha is None:
        # I prefer TimeSeriesSplit for this since we're dealing with time series data
        tscv = TimeSeriesSplit(n_splits=min(3, len(X_pre) - 1))
        param_grid = {'alpha': np.logspace(-3, 3, 7)}  # Try a range of alphas
        
        if method == 'ridge':
            model = GridSearchCV(
                Ridge(fit_intercept=True, positive=True),  # Positive weights make more sense here
                param_grid,
                cv=tscv,
                scoring='neg_mean_squared_error'
            )
        else:  # method == 'lasso'
            model = GridSearchCV(
                Lasso(fit_intercept=True, positive=True, max_iter=10000),
                param_grid,
                cv=tscv,
                scoring='neg_mean_squared_error'
            )
        
        model.fit(X_pre_scaled, y_pre)
        best_model = model.best_estimator_
        best_alpha = model.best_params_['alpha']
    else:
        # Use provided alpha
        if method == 'ridge':
            best_model = Ridge(alpha=alpha, fit_intercept=True, positive=True)
        else:  # method == 'lasso'
            best_model = Lasso(alpha=alpha, fit_intercept=True, positive=True, max_iter=10000)
        
        best_model.fit(X_pre_scaled, y_pre)
        best_alpha = alpha
    
    # Get model weights
    weights = best_model.coef_
    
    # Calculate MSE on pre-period
    y_pre_pred = best_model.predict(X_pre_scaled)
    mse = np.mean((y_pre - y_pre_pred) ** 2)
    
    # Create full time series pivot
    pivot_full = df.pivot_table(
        index=time_col, 
        columns=geo_col, 
        values=outcome_col,
        aggfunc='mean'
    )
    
    # Generate counterfactual predictions for full time period
    X_full = pivot_full[control_geos].values
    X_full_scaled = scaler.transform(X_full)
    y_pred_full = best_model.predict(X_full_scaled)
    
    # Create results dataframe
    results = pd.DataFrame({
        time_col: pivot_full.index,
        'actual': pivot_full[target_geo].values,
        'counterfactual': y_pred_full,
        'is_post': pivot_full.index > pre_period_end
    })
    
    # Calculate lift in post-period
    post_results = results[results['is_post']]
    if len(post_results) == 0:
        lift = np.nan
    else:
        post_actual_avg = post_results['actual'].mean()
        post_counterfactual_avg = post_results['counterfactual'].mean()
        lift = (post_actual_avg / post_counterfactual_avg) - 1 if post_counterfactual_avg != 0 else np.nan
    
    # Create weights dictionary
    weights_dict = dict(zip(control_geos, weights))
    
    return {
        'model': best_model,
        'alpha': best_alpha,
        'control_geos': control_geos,
        'weights': weights_dict,
        'mse': mse,
        'predictions': results,
        'lift': lift
    }