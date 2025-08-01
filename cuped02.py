import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import scipy.stats as stats











# Load dataset - update path if needed
data = pd.read_csv('data/pre_post_events.csv')
print(f"Loaded {len(data):,} rows with columns: {', '.join(data.columns)}")
data.head()












# Quick data exploration
print("Summary statistics:")
display(data.describe())

# Check treatment distribution
treatment_counts = data['treatment'].value_counts()
print(f"\nTreatment group: {treatment_counts.get(1, 0):,} customers")
print(f"Control group: {treatment_counts.get(0, 0):,} customers")

# Basic visualization of pre/post spend
plt.figure(figsize=(10, 6))
plt.scatter(data['pre_spend'], data['post_spend'], alpha=0.05)
plt.xlabel('Pre-experiment Spend')
plt.ylabel('Post-experiment Spend')
plt.title('Pre vs Post Experiment Spend')
plt.grid(True, alpha=0.3)
plt.show()








# Step 1: Estimate theta using OLS on control data
print("Estimating theta via OLS...")
control_data = data[data['treatment'] == 0]
X = control_data[['pre_spend']]
y = control_data['post_spend']

model = LinearRegression()
model.fit(X, y)
theta = model.coef_[0]

print(f"Estimated theta: {theta:.4f}")
print(f"R² value: {model.score(X, y):.4f}")

# Plot regression line
plt.figure(figsize=(10, 6))
plt.scatter(control_data['pre_spend'], control_data['post_spend'], alpha=0.05)
x_range = np.linspace(control_data['pre_spend'].min(), control_data['pre_spend'].max(), 100)
plt.plot(x_range, model.intercept_ + theta * x_range, 'r-', linewidth=2)
plt.xlabel('Pre-experiment Spend')
plt.ylabel('Post-experiment Spend')
plt.title('Control Group: Pre vs Post with Regression Line')
plt.grid(True, alpha=0.3)
plt.show()









# Step 2: Apply CUPED adjustment
pre_mean = data['pre_spend'].mean()
data['adjusted_post_spend'] = data['post_spend'] - theta * (data['pre_spend'] - pre_mean)

# Calculate treatment effects
treatment_data = data[data['treatment'] == 1]
control_data = data[data['treatment'] == 0]

# Naive treatment effect
naive_effect = treatment_data['post_spend'].mean() - control_data['post_spend'].mean()

# CUPED-adjusted treatment effect
cuped_effect = treatment_data['adjusted_post_spend'].mean() - control_data['adjusted_post_spend'].mean()

print(f"Naive treatment effect: {naive_effect:.4f}")
print(f"CUPED-adjusted treatment effect: {cuped_effect:.4f}")

# Calculate standard errors and confidence intervals
treatment_n = len(treatment_data)
control_n = len(control_data)

# Naive standard error
naive_se = np.sqrt(
    treatment_data['post_spend'].var() / treatment_n + 
    control_data['post_spend'].var() / control_n
)

# CUPED standard error
cuped_se = np.sqrt(
    treatment_data['adjusted_post_spend'].var() / treatment_n + 
    control_data['adjusted_post_spend'].var() / control_n
)

# Variance reduction
variance_reduction = 1 - (cuped_se**2 / naive_se**2)
print(f"Variance reduction from CUPED: {variance_reduction:.2%}")














# Step 3: Calculate lift percentage and confidence intervals
control_mean = control_data['post_spend'].mean()
lift_percentage = (cuped_effect / control_mean) * 100

# 95% confidence interval
lift_ci_lower = (cuped_effect - 1.96 * cuped_se) / control_mean * 100
lift_ci_upper = (cuped_effect + 1.96 * cuped_se) / control_mean * 100

print(f"Lift Percentage: {lift_percentage:.2f}%")
print(f"95% Confidence Interval: [{lift_ci_lower:.2f}%, {lift_ci_upper:.2f}%]")

# Check if treatment effect is statistically significant
p_value = 2 * (1 - stats.norm.cdf(abs(cuped_effect) / cuped_se))
print(f"p-value: {p_value:.4f}")
print(f"The treatment effect is {'statistically significant' if p_value < 0.05 else 'not statistically significant'} at the 5% level.")

# Visualize results
plt.figure(figsize=(12, 6))

# Compare treatment effects
plt.subplot(1, 2, 1)
plt.errorbar(['Naive', 'CUPED'], 
             [naive_effect, cuped_effect],
             yerr=[1.96 * naive_se, 1.96 * cuped_se],
             fmt='o', capsize=10, markersize=10)
plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
plt.title('Treatment Effect Comparison')
plt.ylabel('Treatment Effect')
plt.grid(alpha=0.3)

# Compare variances
plt.subplot(1, 2, 2)
plt.bar(['Naive', 'CUPED'], [naive_se**2, cuped_se**2])
plt.title(f'Variance Reduction: {variance_reduction:.1%}')
plt.ylabel('Variance')
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()












# Create JSON-compatible output for RL service
result = {
    "metric": "spend",
    "lift_percentage": round(lift_percentage, 2),
    "confidence_interval": {
        "lower": round(lift_ci_lower, 2),
        "upper": round(lift_ci_upper, 2)
    },
    "p_value": round(p_value, 4),
    "is_significant": p_value < 0.05,
    "sample_size": treatment_n + control_n,
    "variance_reduction_percentage": round(variance_reduction * 100, 2)
}

print("Final result for RL service:")
print(result)

