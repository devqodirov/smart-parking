import os
import sys
import tempfile

# Use temp file for test database
os.environ["SMART_PARKING_TEST_DB"] = os.path.join(
    tempfile.gettempdir(), f"smart_parking_test_{os.getpid()}.db"
)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_full_flow():
    r = client.post("/api/v1/users/", json={"phone_number": "998901111111", "full_name": "Akbar aka", "role": "owner"})
    assert r.status_code == 200
    owner_id = r.json()["id"]
    print(f"1. Owner created: id={owner_id}")

    r = client.post("/api/v1/users/", json={"phone_number": "998902222222", "full_name": "Bekzod", "role": "driver"})
    assert r.status_code == 200
    driver_id = r.json()["id"]
    print(f"2. Driver created: id={driver_id}")

    r = client.post("/api/v1/parking/", json={
        "owner_id": owner_id, "address": "Chilonzor 12, 5-uy",
        "latitude": 41.2995, "longitude": 69.2401, "hourly_rate": 5000
    })
    assert r.status_code == 201
    spot_id = r.json()["id"]
    assert r.json()["is_occupied"] is False
    print(f"3. Spot created: id={spot_id}")

    r = client.post(f"/api/v1/users/{driver_id}/deposit?amount=50000")
    assert r.status_code == 200
    assert r.json()["new_balance"] == 50000.0
    print(f"4. Deposit: balance=50000")

    r = client.post("/api/v1/booking/", json={"driver_id": driver_id, "parking_spot_id": spot_id, "hours": 2})
    assert r.status_code == 201
    assert r.json()["status"] == "active"
    assert r.json()["total_price"] == 10000.0
    print(f"5. Booking: status=active, price=10000")

    r = client.get("/api/v1/parking/nearby?lat=41.2995&lon=69.2401&radius=5")
    assert r.status_code == 200
    assert len(r.json()) == 0
    print(f"6. Nearby: 0 spots")

    r = client.get("/api/v1/admin/dashboard")
    assert r.status_code == 200
    assert r.json()["total_users"] == 2
    assert r.json()["active_bookings"] == 1
    print(f"7. Dashboard: OK")

    r = client.post("/api/v1/booking/1/release")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    print(f"8. Release: completed")

    r = client.get(f"/api/v1/users/{owner_id}/analytics")
    assert r.status_code == 200
    assert r.json()["total_earnings"] == 8800.0
    print(f"9. Owner earnings: {r.json()['total_earnings']} so'm")

    r = client.patch(f"/api/v1/parking/{spot_id}/sensor-update?occupied=true&battery=90.0")
    assert r.status_code == 200
    assert r.json()["occupied"] is True
    assert r.json()["battery"] == 90.0
    print(f"10. Sensor update: OK")

    print("=== ALL TESTS PASSED ===")


if __name__ == "__main__":
    test_full_flow()
