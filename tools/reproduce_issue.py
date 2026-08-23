from unittest.mock import MagicMock


def test():
    mock_conn = MagicMock()
    # Set up side_effect for fetchone
    mock_conn.execute.return_value.fetchone.side_effect = [("corrupt",), ("ok",)]

    # Simulate first call (main DB)
    cursor1 = mock_conn.execute("PRAGMA integrity_check")
    res1 = str(cursor1.fetchone()[0])
    print(f"Result 1: {res1}")

    # Simulate second call (backup DB)
    cursor2 = mock_conn.execute("PRAGMA integrity_check")
    res2 = str(cursor2.fetchone()[0])
    print(f"Result 2: {res2}")


if __name__ == "__main__":
    test()
