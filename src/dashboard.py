import csv
import os
import sys
from collections import Counter
from datetime import datetime

from flask import Flask, jsonify, render_template

sys.path.append(os.path.dirname(__file__))
from ledger import verify_chain

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
VOTES_CSV = os.path.join(BASE_DIR, 'Votes.csv')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)


def read_votes():
    if not os.path.isfile(VOTES_CSV):
        return []

    with open(VOTES_CSV, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/results')
def api_results():

    votes = read_votes()

    counts = Counter(row['VOTE'] for row in votes)

    total_votes = sum(counts.values())

    result_data = []

    for party, vote_count in counts.items():

        percentage = (
            round((vote_count / total_votes) * 100, 2)
            if total_votes > 0 else 0
        )

        result_data.append({
            'party': party,
            'votes': vote_count,
            'percentage': percentage
        })

    result_data.sort(
        key=lambda x: x['votes'],
        reverse=True
    )

    return jsonify({
        'total_votes': total_votes,
        'results': result_data
    })


@app.route('/api/integrity')
def api_integrity():

    ok, bad_row, message = verify_chain(VOTES_CSV)

    return jsonify({
        'valid': ok,
        'bad_row': bad_row,
        'message': message
    })


@app.route('/api/dashboard')
def dashboard_data():

    votes = read_votes()

    total_votes = len(votes)

    vote_counts = Counter()

    fraud_attempts = 0

    for row in votes:

        vote_counts[row['VOTE']] += 1

        if row.get('STATUS') == 'FRAUD':
            fraud_attempts += 1

    leading_party = "N/A"

    if vote_counts:
        leading_party = vote_counts.most_common(1)[0][0]

    turnout_percentage = min(
        round((total_votes / 100) * 100, 2),
        100
    )

    return jsonify({

        "total_votes": total_votes,

        "total_candidates": len(vote_counts),

        "leading_party": leading_party,

        "fraud_attempts": fraud_attempts,

        "turnout_percentage": turnout_percentage,

        "party_names": list(vote_counts.keys()),

        "party_votes": list(vote_counts.values())
    })


@app.route('/api/analytics')
def analytics():

    votes = read_votes()

    vote_counts = Counter(
        row['VOTE'] for row in votes
    )

    labels = list(vote_counts.keys())

    values = list(vote_counts.values())

    percentages = []

    total = sum(values)

    for value in values:

        if total == 0:
            percentages.append(0)

        else:
            percentages.append(
                round(value * 100 / total, 2)
            )

    return jsonify({
        "labels": labels,
        "values": values,
        "percentages": percentages
    })


@app.route('/api/security')
def security():

    ok, bad_row, message = verify_chain(VOTES_CSV)

    security_score = 100

    if not ok:
        security_score = 50

    return jsonify({

        "blockchain_status":
            "Secure" if ok else "Tampered",

        "security_score":
            security_score,

        "message":
            message,

        "bad_row":
            bad_row
    })


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5001
    )