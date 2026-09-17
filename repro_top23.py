import pandas as pd

df = pd.DataFrame([
    {'Player': 'Casemiro', 'Club': 'Manchester United', 'Nation': 'Brazil', 'League': 'English League', 'Rating': 97, 'Epic_Priority': 0, 'Effective_Club_Rating': 97, 'Top23_Count': 1},
    {'Player': 'Zirkzee', 'Club': 'Manchester United', 'Nation': 'Netherlands', 'League': 'English League', 'Rating': 97, 'Epic_Priority': 1, 'Effective_Club_Rating': 97, 'Top23_Count': 2},
])
print(df.sort_values(['Effective_Club_Rating', 'Top23_Count', 'Epic_Priority'], ascending=[False, False, True])[['Player', 'Top23_Count', 'Epic_Priority']].to_string(index=False))
