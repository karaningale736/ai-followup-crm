from app.services.ai_provider import MockAIProvider, get_ai_provider


def test_mock_provider_used_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)


def test_personalize_fills_known_variables():
    provider = MockAIProvider()
    result = provider.personalize_email({
        "template_subject": "Hi {client_first_name}",
        "template_body": "Regarding {feature_title} for {company_name}.",
        "variables": {"client_first_name": "Amara", "feature_title": "Cover Feature",
                       "company_name": "Northwind"},
    })
    assert result["subject"] == "Hi Amara"
    assert "Cover Feature" in result["email_body"]
    assert "Northwind" in result["email_body"]


def test_personalize_never_invents_missing_fields():
    provider = MockAIProvider()
    result = provider.personalize_email({
        "template_subject": "Offer: {offer_amount}",
        "template_body": "Your price is {offer_amount} {currency}.",
        "variables": {},
    })
    assert "[MISSING: offer_amount]" in result["subject"]
    assert "[MISSING: offer_amount]" in result["email_body"]
    assert "[MISSING: currency]" in result["email_body"]


def test_classify_detects_decline():
    provider = MockAIProvider()
    result = provider.classify_response("We've decided to decline this opportunity.", {})
    assert result["classification"] == "DECLINED"


def test_classify_detects_budget_concern():
    provider = MockAIProvider()
    result = provider.classify_response("The price is a bit higher than our budget.", {})
    assert result["classification"] == "BUDGET_CONCERN"


def test_classify_empty_message_is_no_response():
    provider = MockAIProvider()
    result = provider.classify_response("", {})
    assert result["classification"] == "NO_RESPONSE"
