import numpy as np

def generate_ff_design(num_factors):
    """
    Generate a Resolution-IV fractional factorial design matrix for binary factors.
    """
    if not isinstance(num_factors, int) or num_factors < 2 or num_factors > 6:
        raise ValueError("Number of factors must be between 2 and 6")
    
    # For smaller designs, we can use full factorial
    if num_factors <= 4:
        runs = 2**num_factors
        design = np.zeros((runs, num_factors))
        
        # Generate design using binary representation
        for i in range(runs):
            for j in range(num_factors):
                design[i, j] = 2 * ((i >> j) & 1) - 1
        
        return design
    
    # For 5 factors, use 2^(5-1) design
    elif num_factors == 5:
        # Generate the base design (first 4 columns)
        base = generate_ff_design(4)
        result = np.zeros((16, 5))
        result[:, 0:4] = base
        
        # Define 5th column as product of first 4 (generator: I = ABCDE)
        result[:, 4] = base[:, 0] * base[:, 1] * base[:, 2] * base[:, 3]
        
        return result
    
    # For 6 factors, use 2^(6-2) design
    else:  # num_factors == 6
        # Start with full factorial for 4 factors
        base = generate_ff_design(4)
        result = np.zeros((16, 6))
        result[:, 0:4] = base
        
        # Define 5th column (generator: I = ABCE)
        result[:, 4] = base[:, 0] * base[:, 1] * base[:, 2]
        
        # Define 6th column (generator: I = ABDF)
        result[:, 5] = base[:, 0] * base[:, 1] * base[:, 3]
        
        return result