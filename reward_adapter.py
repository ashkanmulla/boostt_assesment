import json
from google.protobuf.json_format import Parse
from boostt_proto.reward_pb2 import Reward, ExperimentResult, ConfidenceInterval

def convert_lift_to_reward(lift_json, experiment_id=None):
    """
    Convert lift metrics into a gRPC Reward message.
    
    This bridges our analytics pipeline with the RL service.
    """
    # Parse JSON if string is provided
    if isinstance(lift_json, str):
        lift_data = json.loads(lift_json)
    else:
        lift_data = lift_json
    
    # Create reward message
    reward = Reward()
    
    # Set experiment ID
    reward.experiment_id = experiment_id or lift_data.get('experiment_id', '')
    
    # Process each metric
    metrics = lift_data.get('metrics', [])
    if not metrics and 'metric' in lift_data:
        # Handle case where lift_data is a single metric
        metrics = [lift_data]
    
    for metric in metrics:
        # Create result for this metric
        result = ExperimentResult()
        
        # Set fields from the metric data
        result.metric_name = metric.get('metric', metric.get('name', ''))
        result.lift_percentage = float(metric.get('lift_percentage', 0.0))
        result.p_value = float(metric.get('p_value', 1.0))
        
        # Set confidence interval
        ci = ConfidenceInterval()
        ci_data = metric.get('confidence_interval', {})
        ci.lower = float(ci_data.get('lower', 0.0))
        ci.upper = float(ci_data.get('upper', 0.0))
        result.confidence_interval.CopyFrom(ci)
        
        # Set significance flag
        result.is_significant = metric.get('is_significant', False)
        
        # Set sample size
        result.sample_size = int(metric.get('sample_size', 0))
        
        # Add to results list
        reward.results.append(result)
    
    # Set experiment factors if available
    factors = lift_data.get('factors', {})
    for key, value in factors.items():
        reward.factors[key] = str(value)
    
    return reward