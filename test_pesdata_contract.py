from app import _extract_pesdata_appearance


def test_extract_pesdata_appearance_from_standard_payload():
    payload = {
        'appearance': {
            'ArmLength': 42,
            'ShoulderWidth': 18,
            'LegLength': 95,
        }
    }
    assert _extract_pesdata_appearance(payload) == payload['appearance']


def test_extract_pesdata_appearance_from_nested_data_payload():
    payload = {
        'data': {
            'appearance': {
                'ArmLength': 41,
                'ShoulderWidth': 17,
            }
        }
    }
    assert _extract_pesdata_appearance(payload) == payload['data']['appearance']


def test_extract_pesdata_appearance_from_alternate_keys():
    payload = {
        'bodyModel': {
            'armLength': 39,
            'shoulderWidth': 16,
        }
    }
    assert _extract_pesdata_appearance(payload) == payload['bodyModel']


def test_extract_pesdata_appearance_returns_empty_dict_for_non_matching_payload():
    assert _extract_pesdata_appearance({'status': 'ok', 'message': 'no player'}) == {}
