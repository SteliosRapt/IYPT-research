from simulation_code import PipeGeometry
import numpy as np

h1 = 0.2
nodes = np.array([
    [0.0, 0.1],   # A
    [0.03, h1],   # B
    [0.06, -0.2], # C
    [0.09, 0.5],  # D crest
    [0.30, -0.1], # E
])

geom = PipeGeometry(nodes, h1_for_validation=h1)
print('S:', geom.S)
