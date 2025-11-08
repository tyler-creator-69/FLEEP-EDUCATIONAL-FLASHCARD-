from datetime import datetime

# Simple SM-2 inspired implementation

def review(card_row, quality):
    """
    card_row: sqlite row with fields including 'ease','interval','reps'
    quality: 0..5
    returns (ease, interval, reps, due_date)
    """
    try:
        ease = float(card_row['ease'])
        interval = int(card_row['interval'])
        reps = int(card_row['reps'])
    except Exception:
        ease, interval, reps = 2.5, 1, 0

    if quality < 3:
        reps = 0
        interval = 1
    else:
        reps += 1
        ease = max(1.3, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = int(interval * ease)

    due = datetime.utcnow().strftime('%Y-%m-%d')
    return ease, interval, reps, due
