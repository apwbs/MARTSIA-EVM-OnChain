from itertools import combinations

def policy_plus(policy, num_Auth):
    policy_Split = [f.strip("()") for seen in [set()] for f in policy.split(" ") if f not in {"or", "and"} and "+" in f and f not in seen and not seen.add(f)]
    for formula in policy_Split:
        name, value = formula.strip("+").split("@")
        authorities = [f"{name}@AUTH{i+1}" for i in range(int(num_Auth))]
        if value == "1":
            transformation = f"({ ' or '.join(authorities) })"
        elif value == num_Auth:
            transformation = f"({ ' and '.join(authorities) })"
        else:
            authority_combinations = combinations(authorities, int(value))
            transformation = "(" + ' or '.join([f"({' and '.join(comb)})" for comb in authority_combinations]) + ")"
        policy = policy.replace(formula, transformation)
    return policy