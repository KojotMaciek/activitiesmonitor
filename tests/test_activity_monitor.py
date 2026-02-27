import pytest

from activity_monitor import (
    build_activities_query,
    create_activities_table,
    create_db_connection,
    fetch_activities,
    format_minutes_to_hhmm,
    insert_activity_record,
    parse_duration_to_minutes,
    parse_pace_to_min_per_km,
)


def test_parse_duration_to_minutes_supports_hhmm_and_hhmmss_and_decimal() -> None:
    assert parse_duration_to_minutes("1:30") == 90
    assert parse_duration_to_minutes("1:30:30") == pytest.approx(90.5)
    assert parse_duration_to_minutes("95.5") == pytest.approx(95.5)


def test_parse_duration_to_minutes_invalid_format_raises() -> None:
    with pytest.raises(ValueError):
        parse_duration_to_minutes("1:2:3:4")


def test_parse_pace_to_min_per_km_supports_mmss_and_decimal() -> None:
    assert parse_pace_to_min_per_km("8:30") == pytest.approx(8.5)
    assert parse_pace_to_min_per_km("7.75") == pytest.approx(7.75)


def test_parse_pace_to_min_per_km_invalid_format_raises() -> None:
    with pytest.raises(ValueError):
        parse_pace_to_min_per_km("1:2:3")


def test_format_minutes_to_hhmm() -> None:
    assert format_minutes_to_hhmm(90) == "01:30"
    assert format_minutes_to_hhmm(125.4) == "02:05"


def test_build_activities_query_with_filters() -> None:
    query, params = build_activities_query(
        activity_filter="cycling",
        from_date="2026-01-01",
        to_date="2026-01-31",
        min_dist="10",
        max_dist="80",
    )

    assert "activity_type = ?" in query
    assert "activity_date >= ?" in query
    assert "activity_date <= ?" in query
    assert "distance_km >= ?" in query
    assert "distance_km <= ?" in query
    assert params == ["cycling", "2026-01-01", "2026-01-31", 10.0, 80.0]


def test_build_activities_query_invalid_date_raises() -> None:
    with pytest.raises(ValueError):
        build_activities_query(from_date="2026/01/01")


def test_db_flow_uses_test_db_file(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    conn = create_db_connection(str(db_path))
    create_activities_table(conn)

    insert_activity_record(
        conn,
        activity_date="2026-01-10",
        activity_type="cycling",
        distance_km=42.0,
        avg_metric_value=28.0,
        avg_metric_unit="km/h",
        total_minutes=90.0,
        calories=950,
        created_at="2026-01-10T10:00:00",
    )
    insert_activity_record(
        conn,
        activity_date="2026-01-12",
        activity_type="walking",
        distance_km=8.5,
        avg_metric_value=10.2,
        avg_metric_unit="min/km",
        total_minutes=87.0,
        calories=430,
        created_at="2026-01-12T10:00:00",
    )

    all_rows = fetch_activities(conn)
    assert len(all_rows) == 2

    cycling_rows = fetch_activities(conn, activity_filter="cycling")
    assert len(cycling_rows) == 1
    assert cycling_rows[0][2] == "cycling"

    long_rows = fetch_activities(conn, min_dist="10")
    assert len(long_rows) == 1
    assert long_rows[0][3] == pytest.approx(42.0)

    conn.close()
    assert db_path.exists()
