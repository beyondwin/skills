"""Pure image-review metrics; no provider, filesystem, product or private paths.

Reference rows: id, eligible (bool or None for disputed), category (string).
Observation rows: id, eligible (bool), unverified (bool; defaults False).
Missing observations retain the reference denominator. Positive holds, including
unverified rejections, are false rejects. Negative unverified holds are not
false accepts, but are never correct negatives. Disputed gold stays unscored.
"""
import math


def _index(rows, label):
    if not isinstance(rows, list):
        raise ValueError(label + ' must be a list')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] or row['id'] in result:
            raise ValueError('Invalid or duplicate ' + label + ' id')
        result[row['id']] = row
    return result


def score(reference, observations):
    gold = _index(reference, 'reference')
    predicted = _index(observations, 'observation')
    if set(predicted) - set(gold):
        raise ValueError('Unexpected observation id')
    items = []
    for ident, ref in gold.items():
        actual = ref.get('eligible')
        if actual is not None and type(actual) is not bool:
            raise ValueError('Reference eligibility must be bool or null')
        if 'eligible' not in ref or not isinstance(ref.get('category'), str):
            raise ValueError('Reference missing eligibility or category')
        row = predicted.get(ident)
        missing = row is None
        unknown = False
        if row is not None:
            if type(row.get('eligible')) is not bool or type(row.get('unverified', False)) is not bool:
                raise ValueError('Invalid observed eligibility or uncertainty')
            unknown = row.get('unverified', False)
            if row['eligible'] and unknown:
                raise ValueError('Eligible contradicts unverified critical condition')
        choice = row['eligible'] if row is not None else None
        correct = False
        if actual is None:
            outcome = 'disputed_reference'
        elif missing:
            outcome = 'missing_positive' if actual else 'missing_negative'
        elif unknown:
            outcome = 'false_reject' if actual else 'negative_unverified'
        else:
            correct = choice == actual
            outcome = ('true_accept' if choice else 'false_reject') if actual else ('false_accept' if choice else 'true_reject')
        items.append({'id': ident, 'category': ref['category'], 'reference_eligible': actual,
                      'observed_eligible': choice, 'missing': missing, 'unverified': unknown,
                      'correct': correct, 'classification': outcome})
    counts = {}
    for row in items:
        counts[row['classification']] = counts.get(row['classification'], 0) + 1
    clear = sum(row['reference_eligible'] is not None for row in items)
    correct = sum(row['correct'] for row in items)
    categories = {}
    for name in sorted({row['category'] for row in items}):
        subset = [row for row in items if row['category'] == name]
        categories[name] = {'total': len(subset), 'clear': sum(r['reference_eligible'] is not None for r in subset),
                            'correct': sum(r['correct'] for r in subset),
                            'errors': sum(r['reference_eligible'] is not None and not r['correct'] for r in subset)}
    return {'total': len(items), 'clear': clear, 'disputed': len(items) - clear,
            'observed': len(predicted), 'missing': sum(r['missing'] for r in items),
            'correct': correct, 'accuracy_on_clear': correct / clear if clear else None,
            'accuracy_on_all': correct / len(items) if items else None,
            'false_accept': counts.get('false_accept', 0),
            'false_reject': counts.get('false_reject', 0) + counts.get('missing_positive', 0),
            'unverified': sum(r['unverified'] for r in items),
            'counts': counts, 'categories': categories, 'items': items}


def exact_paired_p(improved, regressed):
    """Two-sided exact sign/McNemar test; each discordant image counted once."""
    if type(improved) is not int or type(regressed) is not int or min(improved, regressed) < 0:
        raise ValueError('Paired counts must be non-negative integers')
    total = improved + regressed
    if not total:
        return 1.0
    return min(1.0, 2.0 * sum(math.comb(total, k) for k in range(min(improved, regressed) + 1)) / 2 ** total)


def compare_repetitions(reference, baseline_repetitions, candidate_repetitions):
    """Report every repetition, then one paired outcome per unique clear image.

The aggregate compares per-image correct-decision fractions across repetitions.
It does not treat repeated reviews as additional independent images. Disputed
reference labels retain total population but never supply an improvement.
"""
    if not isinstance(baseline_repetitions, list) or not baseline_repetitions or len(baseline_repetitions) != len(candidate_repetitions):
        raise ValueError('Equal nonempty repetition lists required')
    baseline = [score(reference, rows) for rows in baseline_repetitions]
    candidate = [score(reference, rows) for rows in candidate_repetitions]
    by_arm = [[{row['id']: row for row in run['items']} for run in runs] for runs in [baseline, candidate]]
    repetitions = []
    for old, new in zip(baseline, candidate):
        previous = {row['id']: row for row in old['items']}
        improved = sum(row['correct'] and not previous[row['id']]['correct'] for row in new['items'])
        regressed = sum(not row['correct'] and previous[row['id']]['correct'] for row in new['items'])
        repetitions.append({'baseline': old, 'candidate': new, 'improved_unique': improved,
                            'regressed_unique': regressed, 'net_correct_gain': improved-regressed,
                            'exact_paired_p': exact_paired_p(improved, regressed)})
    unique = []
    for ref in reference:
        ident = ref['id']
        old = sum(run[ident]['correct'] for run in by_arm[0]) / len(baseline)
        new = sum(run[ident]['correct'] for run in by_arm[1]) / len(candidate)
        outcome = 'disputed' if ref['eligible'] is None else 'improved' if new > old else 'regressed' if new < old else 'tied'
        unique.append({'id': ident, 'baseline_correct_fraction': old, 'candidate_correct_fraction': new, 'outcome': outcome})
    improved = sum(row['outcome']=='improved' for row in unique)
    regressed = sum(row['outcome']=='regressed' for row in unique)
    return {'repetitions': repetitions, 'unique_population': len(reference),
            'unique_clear_population': baseline[0]['clear'], 'reviews_per_image_per_arm': len(baseline),
            'unique_improved': improved, 'unique_regressed': regressed,
            'unique_exact_paired_p': exact_paired_p(improved, regressed), 'unique_items': unique,
            'unit_of_analysis': 'unique source image; repetition is not another independent image'}
