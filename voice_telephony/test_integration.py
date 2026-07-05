from types import SimpleNamespace

import app as kisan_app


def assert_contains(text, expected, label):
    if expected not in text:
        raise AssertionError(f"{label} missing expected text: {expected}")


def run_test(name, test_func):
    try:
        test_func()
        print(f"[PASS] {name}")
        return True
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        return False


def main():
    sent_messages = []
    original_sms_sender = kisan_app.send_advisory_sms
    original_advisory_url = kisan_app.ADVISORY_ENGINE_URL

    def fake_send_advisory_sms(to_number, message_body):
        sent_messages.append({"to": to_number, "body": message_body})
        return SimpleNamespace(sid="SM_TEST_123")

    kisan_app.send_advisory_sms = fake_send_advisory_sms
    kisan_app.ADVISORY_ENGINE_URL = None
    client = kisan_app.app.test_client()

    def test_send_advisory_endpoint():
        sent_messages.clear()
        response = client.post(
            "/send-advisory",
            json={
                "to": "+919999999999",
                "advisory": "Kal baarish ki sambhavna hai. Sinchai rok dein.",
            },
        )
        data = response.get_json()

        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        if data.get("status") != "sent":
            raise AssertionError(f"Unexpected status payload: {data}")
        if len(sent_messages) != 1:
            raise AssertionError("SMS sender was not called exactly once")

    def test_voice_webhook():
        response = client.post("/voice", data={"From": "+919999999999"})
        body = response.get_data(as_text=True)

        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        assert_contains(body, "<Gather", "voice TwiML")
        assert_contains(body, "/menu", "voice TwiML")
        assert_contains(body, "Kisan Alert", "voice greeting")

    def test_menu_disease_option():
        sent_messages.clear()
        response = client.post(
            "/menu",
            data={"Digits": "1", "From": "+919999999999"},
        )
        body = response.get_data(as_text=True)

        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        assert_contains(body, "blight rog paaya gaya hai", "disease advisory")
        assert_contains(body, "SMS mein bhi bheji ja rahi hai", "disease SMS notice")
        if len(sent_messages) != 1:
            raise AssertionError("Disease flow did not trigger exactly one SMS")

    def test_menu_general_option():
        sent_messages.clear()
        response = client.post(
            "/menu",
            data={"Digits": "2", "From": "+919999999999"},
        )
        body = response.get_data(as_text=True)

        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        assert_contains(body, "Agle teen dinon mein baarish ki sambhavna hai", "general advisory")
        assert_contains(body, "SMS mein bhi bheji ja rahi hai", "general SMS notice")
        if len(sent_messages) != 1:
            raise AssertionError("General flow did not trigger exactly one SMS")

    tests = [
        ("POST /send-advisory sends sample advisory", test_send_advisory_endpoint),
        ("POST /voice returns TwiML gather menu", test_voice_webhook),
        ("POST /menu with digit 1 returns disease advisory", test_menu_disease_option),
        ("POST /menu with digit 2 returns general advisory", test_menu_general_option),
    ]

    passed = 0
    total = len(tests)

    try:
        for name, test_func in tests:
            if run_test(name, test_func):
                passed += 1
    finally:
        kisan_app.send_advisory_sms = original_sms_sender
        kisan_app.ADVISORY_ENGINE_URL = original_advisory_url

    print(f"\nSummary: {passed}/{total} tests passed.")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
