# -*- coding: utf-8 -*-
"""
Test Beam Search booster synergy optimization.

This test creates a synthetic scenario where:
- Greedy selection (high base rating) → Total ~2210
- Booster-aware selection (synergy unlock) → Total ~2235+

If Beam Search finds the synergy solution, it demonstrates the algorithm
is actually optimizing for cascading booster effects, not just high base ratings.
"""

import pandas as pd
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import (
    _calculate_squad_depths,
    _get_player_boosted_rating,
    _get_squad_total_boosted_rating,
    _beam_search_squad_optimization,
    FORMATIONS,
    _normalize_booster_type
)


def create_synthetic_squad_data():
    """
    Create synthetic player data with known booster synergy.
    
    Scenario:
    - Player A: Rating 97, Nation France, no booster
    - Players X1-X10: Rating 88-90, Nation Spain, WITH National booster
      - Booster Rating 1-7: base (no boost)
      - Booster Rating 8-10: +8
      - Booster Rating 11-23: +10
    
    Expected outcomes:
    1. GREEDY (pick A + others): 
       Spain depth = 1 (no tier boost)
       Total ≈ 97 + 88*5 + lower players ≈ 2180-2200
    
    2. SYNERGY (pick X1-X10 + others):
       Spain depth = 10 (tier 8-10 or higher)
       Each X player: 88 + 8 = 96
       Total ≈ 96*10 + other bench ≈ 2230+
    """
    
    players = []
    player_id = 1000
    
    # High base rating but no synergy
    players.append({
        'Player': 'Player_A_HighBase',
        'Player ID': str(player_id),
        'Player URL': '',
        'Position': 'CF',
        'Real_Position': 'CF',
        'Secondary Positions': '',
        'Rating': 97,
        'Effective_Nation_Rating': 97,
        'Effective_Club_Rating': 97,
        'Effective_League_Rating': 97,
        'Height': '185',
        'Weight': '80',
        'Age': '28',
        'Nation': 'France',
        'Club': 'Club_A',
        'League': 'League_A',
        'Player Type': 'Base',
        'Booster Type': 'None',
        'Booster Rating 1-7': 0,
        'Booster Rating 8-10': 0,
        'Booster Rating 11-23': 0,
        'National Booster': False,
        'Data': {}
    })
    player_id += 1
    
    # Spain national booster players (synergy potential)
    for i in range(10):
        players.append({
            'Player': f'Player_Spain_{i+1}',
            'Player ID': str(player_id),
            'Player URL': '',
            'Position': 'CB' if i < 2 else 'CM' if i < 5 else 'LW',
            'Real_Position': 'CB' if i < 2 else 'CM' if i < 5 else 'LW',
            'Secondary Positions': '',
            'Rating': 88,
            'Effective_Nation_Rating': 88,
            'Effective_Club_Rating': 88,
            'Effective_League_Rating': 88,
            'Height': '184',
            'Weight': '79',
            'Age': '26',
            'Nation': 'Spain',
            'Club': 'Club_Spain',
            'League': 'League_Spain',
            'Player Type': 'National Booster',
            'Booster Type': 'National',
            'Booster Rating 1-7': 88,  # No boost in tier 1-7
            'Booster Rating 8-10': 96,  # +8 boost in tier 8-10
            'Booster Rating 11-23': 98,  # +10 boost in tier 11-23
            'National Booster': True,
            'Data': {}
        })
        player_id += 1
    
    # Fill remaining with moderate players
    nations = ['Germany', 'Italy', 'England', 'Portugal', 'Argentina']
    for i in range(12):  # More players for bench
        nation = nations[i % len(nations)]
        players.append({
            'Player': f'Player_{nation}_{i}',
            'Player ID': str(player_id),
            'Player URL': '',
            'Position': 'GK' if i == 0 else 'RB',
            'Real_Position': 'GK' if i == 0 else 'RB',
            'Secondary Positions': '',
            'Rating': 82,
            'Effective_Nation_Rating': 82,
            'Effective_Club_Rating': 82,
            'Effective_League_Rating': 82,
            'Height': '180',
            'Weight': '78',
            'Age': '25',
            'Nation': nation,
            'Club': f'Club_{nation}',
            'League': f'League_{nation}',
            'Player Type': 'Base',
            'Booster Type': 'None',
            'Booster Rating 1-7': 0,
            'Booster Rating 8-10': 0,
            'Booster Rating 11-23': 0,
            'National Booster': False,
            'Data': {}
        })
        player_id += 1
    
    df = pd.DataFrame(players)
    
    # Ensure Data column contains dict representation
    for idx, row in df.iterrows():
        df.at[idx, 'Data'] = row.to_dict()
    
    return df


def test_booster_synergy():
    """
    Test: Does Beam Search find the booster synergy squad?
    """
    print("\n" + "="*80)
    print("TEST: Beam Search Booster Synergy Detection")
    print("="*80)
    
    df = create_synthetic_squad_data()
    formation = '4-2-3-1'
    
    print(f"\nFormation: {formation}")
    print(f"Required positions: {FORMATIONS[formation]}")
    
    # Calculate expected outcomes
    print("\n--- EXPECTED OUTCOMES ---")
    print("\nScenario 1: GREEDY (High base rating A)")
    greedy_squad = [
        {'Player': 'Player_A_HighBase', 'Data': df[df['Player'] == 'Player_A_HighBase'].iloc[0].to_dict(), 'Is_Starter': True, 'Position': 'CF'},
        {'Player': 'Player_Germany_0', 'Data': df[df['Player'] == 'Player_Germany_0'].iloc[0].to_dict(), 'Is_Starter': True, 'Position': 'GK'},
    ]
    # ... simplified for demo
    print("  Greedy picks: High base rating (97) France CF")
    print("  Spain synergy: No depth bonus (only 1 Spain player)")
    print("  Expected total: ~2180-2200")
    
    print("\nScenario 2: SYNERGY-AWARE (Multiple Spain boosters)")
    print("  Synergy picks: Multiple Spain National boosters")
    print("  Spain depth: 10 → Tier 8-10 activated")
    print("  Each Spain player: 88 + 8 = 96 (vs 88 in greedy)")
    print("  Boost gain: 10 players * 8 = +80 total")
    print("  Expected total: ~2260-2280")
    
    # Run Beam Search
    print("\n--- RUNNING BEAM SEARCH ---")
    print(f"Dataset: {len(df)} players")
    print(f"Formation: {formation}")
    
    best_squad = _beam_search_squad_optimization(
        df,
        FORMATIONS[formation],
        sort_mode='rating_desc',
        formation_name=formation,
        beam_width=10,
        max_iterations=5
    )
    
    if not best_squad:
        print("ERROR: Beam Search returned None!")
        return False
    
    # Analyze result
    print("\n--- BEAM SEARCH RESULT ---")
    total_rating = _get_squad_total_boosted_rating(best_squad)
    print(f"Total boosted rating: {total_rating}")
    
    # Count nations
    spain_count = sum(1 for p in best_squad if p.get('Player') and p['Player'].startswith('Player_Spain'))
    france_count = sum(1 for p in best_squad if p.get('Player') and p['Player'].startswith('Player_A'))
    
    print(f"Spain players in squad: {spain_count}")
    print(f"France (high-base) players in squad: {france_count}")
    
    # Check squad composition
    starters = [p for p in best_squad if p.get('Is_Starter', False) and p['Player'] != '---']
    print(f"\nStarters count: {len(starters)}")
    for p in starters[:5]:
        print(f"  - {p['Player']}")
    
    # Evaluate: Does it prefer synergy?
    if spain_count >= 8 and total_rating >= 2200:
        print("\n✅ SUCCESS: Beam Search detected booster synergy!")
        print(f"   Spain booster depth unlocked: {spain_count} players")
        print(f"   Total boosted rating: {total_rating} (> 2200 threshold)")
        return True
    else:
        print("\n❌ INCONCLUSIVE: Beam Search may not be optimizing booster synergy")
        print(f"   Spain count: {spain_count} (expected >=8)")
        print(f"   Total: {total_rating} (expected >=2200)")
        return False


if __name__ == '__main__':
    success = test_booster_synergy()
    sys.exit(0 if success else 1)
