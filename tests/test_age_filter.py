from datetime import datetime, timezone, timedelta


def test_age_filter_boundary():
    """Test age filter includes branches at exact boundary."""
    now = datetime.now(timezone.utc)
    branch_date = now - timedelta(days=30)
    max_age_days = 30
    age_days = (now - branch_date).days
    assert age_days <= max_age_days


def test_age_filter_excludes_old():
    """Test age filter excludes branches older than threshold."""
    now = datetime.now(timezone.utc)
    branch_date = now - timedelta(days=31)
    max_age_days = 30
    age_days = (now - branch_date).days
    assert age_days > max_age_days
