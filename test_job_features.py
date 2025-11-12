#!/usr/bin/env python3
"""
Manual test script for job priorities and cancellation features.
Run with: python test_job_features.py
"""

import time
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"


def test_priority_upload():
    """Test uploading with different priorities."""
    print("\n=== Testing Priority Upload ===")

    with Path("g-code/3DBenchy_PLA_NoScripts.gcode").open("rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": ("test.gcode", f)},
            data={
                "start_at_layer": 0,
                "extrusion_multiplier": 1.0,
                "priority": 0,  # High priority
            },
        )

    if response.status_code == 202:
        job = response.json()
        print(f"✅ Upload successful: job_id={job['job_id']}, priority={job['priority']}")
        return job["job_id"]
    else:
        print(f"❌ Upload failed: {response.status_code} {response.text}")
        return None


def test_cancel_pending_job():
    """Test cancelling a pending job immediately after upload."""
    print("\n=== Testing Pending Job Cancellation ===")

    # Upload file
    with Path("g-code/3DBenchy_PLA_NoScripts.gcode").open("rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": ("test.gcode", f)},
            data={
                "start_at_layer": 0,
                "extrusion_multiplier": 1.0,
                "priority": 2,  # Low priority
            },
        )

    if response.status_code != 202:
        print(f"❌ Upload failed: {response.status_code}")
        return

    job_id = response.json()["job_id"]
    print(f"📤 Uploaded job {job_id}")

    # Cancel immediately (should be pending)
    cancel_response = requests.post(f"{BASE_URL}/cancel/{job_id}")

    if cancel_response.status_code == 200:
        result = cancel_response.json()
        print(f"✅ Cancellation successful: status={result['status']}")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Cancellation failed: {cancel_response.status_code}")

    # Verify status
    status_response = requests.get(f"{BASE_URL}/status/{job_id}")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"📊 Final status: {status['status']}")


def test_cancel_processing_job():
    """Test cancelling a job while it's processing."""
    print("\n=== Testing Processing Job Cancellation ===")

    # Upload file
    with Path("g-code/3DBenchy_PLA_NoScripts.gcode").open("rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": ("test.gcode", f)},
            data={
                "start_at_layer": 0,
                "extrusion_multiplier": 1.0,
                "priority": 1,  # Normal priority
            },
        )

    if response.status_code != 202:
        print(f"❌ Upload failed: {response.status_code}")
        return

    job_id = response.json()["job_id"]
    print(f"📤 Uploaded job {job_id}")

    # Wait a bit for processing to start
    print("⏳ Waiting 2 seconds for processing to start...")
    time.sleep(2)

    # Check if processing
    status_response = requests.get(f"{BASE_URL}/status/{job_id}")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"📊 Current status: {status['status']}")

    # Cancel
    cancel_response = requests.post(f"{BASE_URL}/cancel/{job_id}")

    if cancel_response.status_code == 200:
        result = cancel_response.json()
        print(f"✅ Cancellation requested: status={result['status']}")
        print(f"   Message: {result['message']}")

        # Poll status until cancelled
        print("⏳ Waiting for cancellation to complete...")
        for i in range(10):
            time.sleep(1)
            status_response = requests.get(f"{BASE_URL}/status/{job_id}")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   [{i + 1}] Status: {status['status']}")
                if status["status"] == "cancelled":
                    print("✅ Job successfully cancelled")
                    break
        else:
            print("⚠️  Timeout waiting for cancellation")
    else:
        print(f"❌ Cancellation failed: {cancel_response.status_code}")


def test_cannot_cancel_completed():
    """Test that completed jobs cannot be cancelled."""
    print("\n=== Testing Cannot Cancel Completed Job ===")

    # Upload and wait for completion
    with Path("g-code/3DBenchy_PLA_NoScripts.gcode").open("rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": ("test.gcode", f)},
            data={
                "start_at_layer": 0,
                "extrusion_multiplier": 1.0,
                "priority": 0,  # High priority
            },
        )

    if response.status_code != 202:
        print(f"❌ Upload failed: {response.status_code}")
        return

    job_id = response.json()["job_id"]
    print(f"📤 Uploaded job {job_id}")

    # Wait for completion
    print("⏳ Waiting for job to complete...")
    for _ in range(30):
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/status/{job_id}")
        if status_response.status_code == 200:
            status = status_response.json()
            if status["status"] in ["completed", "failed"]:
                print(f"✅ Job {status['status']}")
                break
    else:
        print("⚠️  Timeout waiting for completion")
        return

    # Try to cancel
    cancel_response = requests.post(f"{BASE_URL}/cancel/{job_id}")

    if cancel_response.status_code == 409:
        print("✅ Cannot cancel completed job (expected 409 Conflict)")
        error = cancel_response.json()
        print(f"   Detail: {error['detail']}")
    else:
        print(f"❌ Unexpected response: {cancel_response.status_code}")


def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️  Server returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Start with: uvicorn app.main:app --reload")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Background Job Features Test Suite")
    print("=" * 60)

    if not check_server():
        return

    try:
        # Test 1: Priority upload
        test_priority_upload()

        # Test 2: Cancel pending job
        test_cancel_pending_job()

        # Test 3: Cancel processing job
        test_cancel_processing_job()

        # Test 4: Cannot cancel completed
        test_cannot_cancel_completed()

        print("\n" + "=" * 60)
        print("✅ All tests completed")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
