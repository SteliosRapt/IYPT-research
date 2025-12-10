from simulation_code import PipeGeometry, SiphonParams, compute_ideal_bound
import numpy as np

h1 = 0.2
# Respect geometry constraints from validate_geometry_constraints
nodes = np.array([
    [0.0, 0.1],   # A
    [0.03, h1],   # B at water level
    [0.06, -0.2], # C low
    [0.09, 0.5],  # D crest
    [0.30, -0.1], # E second-lowest but above C
])

geom = PipeGeometry(nodes, h1_for_validation=h1)
params = SiphonParams(geometry=geom, h1=h1, L1=geom.S[1])

h_max, L_stall, can_prime = compute_ideal_bound(params)
print('h_max', h_max)
print('L_stall', L_stall)
print('can_prime', can_prime)
print('h_crest', params.h_crest)
print('L_crest', params.geometry.L_crest)
