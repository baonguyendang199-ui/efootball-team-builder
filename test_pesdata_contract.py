from app import _extract_pesdata_appearance, extract_efhub_body_model


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


def test_extract_efhub_body_model_from_html():
    html = '''
    <div>
      <h3>Player Model</h3>
      <div>
        <div><span>Arm Length</span><span>8</span></div>
        <div><span>Shoulder Width</span><span>8</span></div>
      </div>
      <h3>Physics</h3>
      <div>
        <div><span>Jumping Height</span><span>275.7</span></div>
      </div>
    </div>
    '''
    result = extract_efhub_body_model(html)
    assert result['Arm Length'] == '8'
    assert result['Shoulder Width'] == '8'
    assert result['Jumping Height'] == '275.7'
