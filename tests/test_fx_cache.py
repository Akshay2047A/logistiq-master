import time
import unittest
from unittest import mock
import streamlit as st

# We'll test the logistiq/utils/data.py implementation of get_live_exchange_rate
from logistiq.utils.data import get_live_exchange_rate

class TestFxCache(unittest.TestCase):
    def setUp(self):
        # Setup state
        if "st.session_state" not in globals() and not hasattr(st, "session_state"):
            pass
            
    @mock.patch("logistiq.utils.data.requests.get")
    @mock.patch("logistiq.utils.data.time.time")
    def test_fx_returns_cached_within_ttl(self, mock_time, mock_get):
        # Mock current time
        mock_time.return_value = 1000.0
        
        # Seed the cache
        st.session_state._fx_rate = 82.0
        st.session_state._fx_ts = 900.0 # 100 seconds ago, within 600s TTL
        
        rate = get_live_exchange_rate()
        
        # Assert returns cached value
        self.assertEqual(rate, 82.0)
        # Assert did not call API
        mock_get.assert_not_called()

    @mock.patch("logistiq.utils.data.requests.get")
    @mock.patch("logistiq.utils.data.time.time")
    def test_fx_refreshes_after_ttl_expires(self, mock_time, mock_get):
        # Mock current time
        mock_time.return_value = 2000.0
        
        # Seed the cache with expired timestamp
        st.session_state._fx_rate = 82.0
        st.session_state._fx_ts = 1000.0 # 1000 seconds ago, expired
        
        # Mock API response
        mock_resp = mock.Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"rates": {"INR": 83.5}}
        mock_get.return_value = mock_resp
        
        rate = get_live_exchange_rate()
        
        # Assert returns new value
        self.assertEqual(rate, 83.5)
        # Assert called API
        mock_get.assert_called_once()
        # Assert cache updated
        self.assertEqual(st.session_state._fx_rate, 83.5)
        self.assertEqual(st.session_state._fx_ts, 2000.0)

if __name__ == '__main__':
    unittest.main()
