"""
HOLDOUT VALIDATION
==================
Tests the pattern estimator on held-out database entries.

Methodology:
1. Randomly select 25 people from the database
2. Temporarily remove them
3. Run pattern estimator on them (treating as unknown)
4. Compare predictions to actual manual estimates
5. Compute accuracy metrics
6. Restore database
"""

import json
import random
import shutil
import os
import sys
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engines import PatternEstimatorV2

DB_PATH = "data/manual_estimates/manual_knowledge.json"
BACKUP_PATH = "data/manual_estimates/manual_knowledge_backup.json"
HOLDOUT_SIZE = 25


def run_holdout():
    print("=" * 70)
    print("HOLDOUT VALIDATION")
    print("=" * 70)

    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f"✓ Backed up database")

    with open(DB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    people = data['people']
    total = len(people)
    print(f"✓ Total people: {total}")

    random.seed(42)
    holdout_indices = random.sample(range(total), HOLDOUT_SIZE)
    holdout_people = [people[i] for i in holdout_indices]
    remaining = [p for i, p in enumerate(people) if i not in holdout_indices]

    print(f"✓ Holding out {len(holdout_people)}, training on {len(remaining)}")

    data['people'] = remaining
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Removed holdout from database")

    print("\n" + "=" * 70)
    print("RUNNING PREDICTIONS")
    print("=" * 70)

    estimator = PatternEstimatorV2()
    results = []

    for person in holdout_people:
        name = person['name']
        actual_mid = person['manual_net_worth'][1]
        entity_type = person.get('entity_type', 'rapper')

        # Simulate YouTube data from actual net worth
        type_mult = {
            'rapper': 80000, 'producer': 30000,
            'media_personality': 100000, 'boxer': 10000, 'singer': 80000
        }.get(entity_type, 50000)

        est_subs = actual_mid * type_mult / 1_000_000
        youtube_data = {
            'subscribers': int(est_subs),
            'total_views': int(est_subs * 800),
            'total_videos': 100
        }

        prediction = estimator.estimate_new_person(name, youtube_data, entity_type)

        if 'error' in prediction:
            results.append({'name': name, 'actual': actual_mid, 'predicted': None, 'error': prediction['error']})
            continue

        pred_mid = prediction['net_worth_range']['mid']
        rel_error = abs(pred_mid - actual_mid) / actual_mid if actual_mid > 0 else 0
        log_error = abs(np.log10(max(pred_mid, 1)) - np.log10(max(actual_mid, 1)))
        within_2x = 0.5 <= (pred_mid / actual_mid) <= 2.0

        results.append({
            'name': name,
            'actual': actual_mid,
            'predicted': pred_mid,
            'rel_error': rel_error,
            'log_error': log_error,
            'within_2x': within_2x
        })

    # Restore
    shutil.copy(BACKUP_PATH, DB_PATH)
    print(f"\n✓ Database restored")

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    valid = [r for r in results if r.get('predicted') is not None]
    if not valid:
        print("❌ No valid predictions")
        return

    median_rel = np.median([r['rel_error'] for r in valid]) * 100
    mean_rel = np.mean([r['rel_error'] for r in valid]) * 100
    mean_log = np.mean([r['log_error'] for r in valid])
    within_2x_pct = np.mean([r['within_2x'] for r in valid]) * 100

    print(f"\nValidation set: {len(valid)} people")
    print(f"Median relative error: {median_rel:.1f}%")
    print(f"Mean relative error: {mean_rel:.1f}%")
    print(f"Log-scale MAE: {mean_log:.3f} (≈ {10**mean_log:.1f}x avg factor)")
    print(f"Within 2× of actual: {within_2x_pct:.0f}%")

    print("\n" + "-" * 70)
    print(f"{'Name':<30} {'Actual':>10} {'Predicted':>10} {'Error':>10}")
    print("-" * 70)

    valid_sorted = sorted(valid, key=lambda x: x['rel_error'], reverse=True)
    for r in valid_sorted:
        within = "✓" if r['within_2x'] else "✗"
        print(f"{r['name'][:30]:<30} ${r['actual']/1e6:>8.1f}M ${r['predicted']/1e6:>8.1f}M {r['rel_error']*100:>8.0f}% {within}")

    report = {
        'validation_size': len(valid),
        'total_holdout': len(holdout_people),
        'median_relative_error_pct': round(median_rel, 1),
        'mean_relative_error_pct': round(mean_rel, 1),
        'log_scale_mae': round(mean_log, 3),
        'avg_error_factor': round(10 ** mean_log, 2),
        'within_2x_pct': round(within_2x_pct, 1),
        'per_person_results': [{k: v for k, v in r.items() if k != 'within_2x'} for r in valid]
    }

    with open("data/holdout_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print(f"✓ Report saved to data/holdout_report.json")
    print("=" * 70)


if __name__ == "__main__":
    run_holdout()