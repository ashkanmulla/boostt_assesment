# Test with sample data
test_lift = {
    "metric": "spend",
    "lift_percentage": 12.5,
    "confidence_interval": {
        "lower": 8.2,
        "upper": 16.8
    },
    "p_value": 0.002,
    "is_significant": True,
    "sample_size": 5000
}

# In a real scenario, you'd have the protobuf library and could do:
# reward = convert_lift_to_reward(test_lift, "experiment_123")
# print(reward)

# For testing without the library:
print("Would convert:", test_lift)
print("Fields that would be set in the Reward message:")
print("- experiment_id: experiment_123")
print("- results[0].metric_name: spend")
print("- results[0].lift_percentage: 12.5")
print("- results[0].confidence_interval.lower: 8.2")
print("- results[0].confidence_interval.upper: 16.8")
print("- results[0].is_significant: True")