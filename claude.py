def find_pairs_with_sum(target_sum, max_val=100):
    """Find all pairs (c,d) where c + d = target_sum and c,d are natural numbers"""
    pairs = []
    for c in range(1, min(target_sum, max_val + 1)):
        d = target_sum - c
        if d > 0 and d <= max_val and c <= d:  # c <= d to avoid duplicates
            pairs.append((c, d))
    return pairs

def find_pairs_with_sum_of_squares(target_sum_sq, max_val=100):
    """Find all pairs (c,d) where c^2 + d^2 = target_sum_sq"""
    pairs = []
    for c in range(1, max_val + 1):
        for d in range(c, max_val + 1):  # d >= c to avoid duplicates
            if c*c + d*d == target_sum_sq:
                pairs.append((c, d))
            elif c*c + d*d > target_sum_sq:
                break
    return pairs

def solve_riddle(max_search=50):
    """
    Solve the logicians riddle by finding pairs (c,d) where:
    1. A knows c+d and initially can't determine c,d uniquely
    2. B knows c^2+d^2 and initially can't determine c,d uniquely  
    3. After A says "I don't know", B can deduce c,d
    4. After B says "Now I know", A can also deduce c,d
    """
    
    print("Solving the Logicians Riddle...")
    print("=" * 50)
    
    solutions = []
    
    # Check all possible pairs (c,d)
    for c in range(1, max_search + 1):
        for d in range(c, max_search + 1):  # d >= c to avoid checking duplicates
            sum_cd = c + d
            sum_squares = c*c + d*d
            
            # Find all pairs that give the same sum as (c,d)
            sum_pairs = find_pairs_with_sum(sum_cd, max_search)
            
            # Find all pairs that give the same sum of squares as (c,d)
            sq_pairs = find_pairs_with_sum_of_squares(sum_squares, max_search)
            
            # Condition 1: A doesn't know initially (multiple pairs with same sum)
            if len(sum_pairs) <= 1:
                continue
                
            # Condition 2: B doesn't know initially (multiple pairs with same sum of squares)  
            if len(sq_pairs) <= 1:
                continue
            
            # Condition 3: After A says "I don't know", B can deduce the answer
            # This means: among all pairs with sum = sum_cd, only (c,d) has sum_of_squares = sum_squares
            valid_for_b = True
            for other_c, other_d in sum_pairs:
                if (other_c, other_d) != (c, d):
                    other_sum_squares = other_c*other_c + other_d*other_d
                    other_sq_pairs = find_pairs_with_sum_of_squares(other_sum_squares, max_search)
                    if len(other_sq_pairs) > 1:
                        valid_for_b = False
                        break
            
            if not valid_for_b:
                continue
                
            # Condition 4: After B says "Now I know", A can deduce the answer
            # This means: among all pairs with sum_squares = sum_squares, only (c,d) has sum = sum_cd
            valid_for_a = True
            for other_c, other_d in sq_pairs:
                if (other_c, other_d) != (c, d):
                    other_sum = other_c + other_d
                    other_sum_pairs = find_pairs_with_sum(other_sum, max_search)
                    if len(other_sum_pairs) > 1:
                        valid_for_a = False
                        break
            
            if valid_for_a:
                solutions.append((c, d, sum_cd, sum_squares))
    
    return solutions

def print_solution_analysis(c, d, sum_cd, sum_squares, max_search=50):
    """Print detailed analysis of a solution"""
    print(f"\nDetailed Analysis for c={c}, d={d}:")
    print(f"A knows: c + d = {sum_cd}")
    print(f"B knows: c² + d² = {sum_squares}")
    
    sum_pairs = find_pairs_with_sum(sum_cd, max_search)
    print(f"\nPairs with sum {sum_cd}: {sum_pairs}")
    print(f"A sees {len(sum_pairs)} possibilities, so A says 'I don't know'")
    
    sq_pairs = find_pairs_with_sum_of_squares(sum_squares, max_search)
    print(f"\nPairs with sum of squares {sum_squares}: {sq_pairs}")
    print(f"B sees {len(sq_pairs)} possibilities initially")
    
    print(f"\nAfter A says 'I don't know', B reasons:")
    print("For each possible sum, B checks if there are multiple sum-of-squares possibilities:")
    
    for other_c, other_d in sum_pairs:
        other_sum_squares = other_c*other_c + other_d*other_d
        other_sq_pairs = find_pairs_with_sum_of_squares(other_sum_squares, max_search)
        print(f"  Sum {sum_cd} could be ({other_c},{other_d}) → sum of squares {other_sum_squares} has {len(other_sq_pairs)} possibilities")
        
    print(f"Only ({c},{d}) is consistent with A not knowing, so B can deduce the answer!")

def main():
    # Solve the riddle
    solutions = solve_riddle(max_search=500)
    
    print(f"\nFound {len(solutions)} solution(s):")
    for i, (c, d, sum_cd, sum_squares) in enumerate(solutions, 1):
        print(f"{i}. c = {c}, d = {d}")
        print(f"   A knows: {sum_cd} (sum)")
        print(f"   B knows: {sum_squares} (sum of squares)")
    
    if solutions:
        # Show detailed analysis for the first solution
        c, d, sum_cd, sum_squares = solutions[0]
        print_solution_analysis(c, d, sum_cd, sum_squares)
    else:
        print("No solutions found in the given range. Try increasing max_search.")

if __name__ == "__main__":
    main()