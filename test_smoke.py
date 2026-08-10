import pandas as pd
import numpy as np
from app import compute_position_model_scores

# Build synthetic DMF group with 12 players
np.random.seed(1)
players = []
for i in range(12):
    h = np.random.randint(170, 195)
    w = np.random.randint(65, 90)
    players.append({
        'Player': f'Player_{i+1}',
        'Position': 'DMF',
        'Rating': np.random.randint(60, 95),
        'Height': h,
        'Weight': w,
        'Arm Length': np.random.uniform(50, 70),
        'Shoulder Width': np.random.uniform(35, 55),
        'Neck Length': np.random.uniform(6, 12),
        'Chest Measurement': np.random.uniform(80, 110),
        'Neck Size': np.random.uniform(32, 42),
        'Shoulder Height': np.random.uniform(90, 110),
        'Leg Length': np.random.uniform(90, 105),
        'Thigh Size': np.random.uniform(45, 60),
        'Waist Size': np.random.uniform(70, 95),
        'Arm Size': np.random.uniform(25, 38),
        'Calf Size': np.random.uniform(30, 42),
        'Leg Coverage Radius': np.random.uniform(60, 120),
        'Arm Coverage Radius': np.random.uniform(40, 90),
        'Jumping Height': np.random.uniform(20, 60),
    })

df = pd.DataFrame(players)
res = compute_position_model_scores(df)
print(res[['Player','Position','Model Score','Model Uniqueness','Model Archetype','model_data_status']])
