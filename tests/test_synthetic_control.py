
import pandas as pd
import numpy as np

# Create sample data
dates = pd.date_range('2023-01-01', '2023-03-31')
geos = ['A', 'B', 'C', 'D']
data = []

for date in dates:
    for geo in geos:
        # Add some treatment effect to geo 'A' after Feb 15
        base = 100 + 10 * np.sin(date.dayofyear / 30)
        treatment = 20 if geo == 'A' and date > pd.Timestamp('2023-02-15') else 0
        noise = np.random.normal(0, 5)
        data.append({
            'date': date,
            'geo': geo,
            'spend': base + treatment + noise
        })

df = pd.DataFrame(data)
result = build_synthetic_control(
    df=df,
    target_geo='A',
    outcome_col='spend',
    time_col='date',
    geo_col='geo',
    pre_period_end=pd.Timestamp('2023-02-15')
)

print(f"Estimated lift: {result['lift']:.2%}")