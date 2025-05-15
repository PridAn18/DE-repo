from dags.example_dag import do_format_data

def test_format_data_output_fields():
    raw_user = {
        "name": {"first": "Anna", "last": "Smith"},
        "gender": "female",
        "location": {
            "street": {"number": 12, "name": "Main St"},
            "city": "TestCity", "state": "TestState", "country": "TestLand", "postcode": "12345"
        },
        "email": "anna.smith@example.com",
        "login": {"username": "asmith"},
        "dob": {"date": "1990-01-01T00:00:00Z"},
        "registered": {"date": "2020-01-01T00:00:00Z"},
        "phone": "123-456-7890",
        "picture": {"medium": "http://example.com/pic.jpg"}
    }

    result = do_format_data(raw_user)

    assert "first_name" in result
    assert result["email"] == "anna.smith@example.com"
    assert result["address"].startswith("12 Main St")