import numpy as np
import pytest
from design import generate_ff_design

def test_design_size():
    """Test that the design matrices have the correct dimensions."""
    for num_factors in range(2, 7):
        design = generate_ff_design(num_factors)
        if num_factors <= 4:
            # Full factorial for 2-4 factors
            expected_rows = 2 ** num_factors
        else:
            # Fractional factorial for 5-6 factors
            expected_rows = 16
        
        assert design.shape == (expected_rows, num_factors), f"Wrong shape for {num_factors} factors"

def test_design_values():
    """Test that the design matrix only contains -1 and 1."""
    for num_factors in range(2, 7):
        design = generate_ff_design(num_factors)
        assert np.all(np.isin(design, [-1, 1])), f"Design for {num_factors} factors contains values other than -1 and 1"

def test_orthogonality():
    """Test that columns are orthogonal (Resolution IV property)."""
    for num_factors in range(2, 7):
        design = generate_ff_design(num_factors)
        
        # Check orthogonality of columns (main effects)
        for i in range(num_factors):
            for j in range(i+1, num_factors):
                dot_product = np.dot(design[:, i], design[:, j])
                assert dot_product == 0, f"Columns {i} and {j} are not orthogonal for {num_factors} factors"

def test_resolution_iv():
    """Test Resolution IV property: main effects not confounded with 2-factor interactions."""
    for num_factors in range(3, 7):  # Skip 2 factors as it's trivial
        design = generate_ff_design(num_factors)
        
        # Check that main effects aren't confounded with 2-factor interactions
        for i in range(num_factors):
            for j in range(num_factors):
                for k in range(j+1, num_factors):
                    if i != j and i != k:
                        # Create two-factor interaction column
                        interaction = design[:, j] * design[:, k]
                        # Check orthogonality with main effect
                        dot_product = np.dot(design[:, i], interaction)
                        assert dot_product == 0, f"Main effect {i} is confounded with interaction {j}×{k}"

def test_invalid_inputs():
    """Test that invalid inputs raise appropriate errors."""
    # Test with too few factors
    with pytest.raises(ValueError):
        generate_ff_design(1)
    
    # Test with too many factors
    with pytest.raises(ValueError):
        generate_ff_design(7)
    
    # Test with non-integer
    with pytest.raises(ValueError):
        generate_ff_design(3.5)