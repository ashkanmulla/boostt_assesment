import pandas as pd
import numpy as np
import os

# Set random seed for reproducibility
np.random.seed(42)

# Parameters
num_customers = 1000000  # 1M customers as per assessment
num_geos = 5
treatment_ratio = 0.5

# Create directory for data if it doesn't exist
os.makedirs('data', exist_ok=True)

print("Generating synthetic dataset with 1M rows...")

# Generate customer IDs
customer_ids = [f'cust_{i:07d}' for i in range(num_customers)]

# Assign treatments (50% treatment, 50% control)
treatments = np.random.binomial(1, treatment_ratio, num_customers)

# Assign geos (balanced across treatment/control)
geos = [f'geo_{np.random.randint(1, num_geos+1)}' for _ in range(num_customers)]

# Generate factors a and b (binary experimental factors)
factor_a = np.random.binomial(1, 0.5, num_customers)
factor_b = np.random.binomial(1, 0.5, num_customers)

# Generate pre-experiment spend
# Log-normal distribution to simulate realistic spending patterns
pre_spend_shape = 1.2
pre_spend_scale = 100
pre_spend = np.random.lognormal(mean=pre_spend_shape, sigma=0.8, size=num_customers) * pre_spend_scale

# Generate post-experiment spend with:
# 1. Strong correlation with pre_spend (theta ~0.7)
# 2. Treatment effect (~10% lift for treated group)
# 3. Realistic noise
theta = 0.7  # Correlation coefficient for CUPED
treatment_effect = 0.10  # 10% lift

# Base post_spend is correlated with pre_spend
post_spend = theta * pre_spend + np.random.lognormal(mean=0, sigma=0.6, size=num_customers) * pre_spend_scale

# Add treatment effect for treatment group
post_spend[treatments == 1] *= (1 + treatment_effect)

# Create DataFrame
data = pd.DataFrame({
    'customer_id': customer_ids,
    'treatment': treatments,
    'pre_spend': pre_spend,
    'post_spend': post_spend,
    'geo': geos,
    'factor_a': factor_a,
    'factor_b': factor_b
})

# Save to CSV
file_path = 'data/pre_post_events.csv'
data.to_csv(file_path, index=False)

print(f"Dataset generated and saved to {file_path}")
print(f"File size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
print("\nSample of generated data:")
print(data.head())
print("\nSummary statistics:")
print(data.describe())

# Verification - Check if CUPED would work with this data
control = data[data['treatment'] == 0]
X = control[['pre_spend']]
y = control['post_spend']

from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X, y)
estimated_theta = model.coef_[0]

print(f"\nEstimated theta: {estimated_theta:.4f} (target was {theta:.4f})")

# Check treatment effect
control_mean = data[data['treatment'] == 0]['post_spend'].mean()
treatment_mean = data[data['treatment'] == 1]['post_spend'].mean()
observed_lift = (treatment_mean / control_mean) - 1

print(f"Observed treatment effect: {observed_lift:.4f} (target was {treatment_effect:.4f})")