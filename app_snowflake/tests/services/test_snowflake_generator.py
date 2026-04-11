"""SnowflakeGenerator tests without snowflake_rw test DB (mocked recount + event hooks)."""

import threading
import time
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_snowflake.tests.conftest import neuter_snowflake_recounter_transaction_for_tests

neuter_snowflake_recounter_transaction_for_tests()

from app_snowflake.consts.snowflake_const import (
    CLOCK_BACKWARD_THRESHOLD,
    MASK_BUSINESS_ID,
    MASK_DATACENTER_ID,
    MASK_MACHINE_ID,
    MASK_SEQUENCE,
)
from app_snowflake.services.snowflake_generator import SnowflakeGenerator


def _clear_snowflake_generator_cache() -> None:
    outer = SnowflakeGenerator._instances
    if SnowflakeGenerator in outer:
        outer[SnowflakeGenerator].clear()


@patch("app_snowflake.services.snowflake_generator.create_or_update_recount", return_value=0)
class TestSnowflakeGenerator(SimpleTestCase):
    def setUp(self):
        super().setUp()
        _clear_snowflake_generator_cache()
        self.datacenter_id = 1
        self.machine_id = 2
        self.business_id = 3
        self.start_timestamp = int(time.time() * 1000)
        self.mock_event_start = MagicMock()
        self.mock_event_clock = MagicMock()
        self.mock_event_seq = MagicMock()
        self._ev_patch = patch.multiple(
            "app_snowflake.services.event_service",
            rec_service_start=self.mock_event_start,
            rec_clock_backward=self.mock_event_clock,
            rec_sequence_overflow=self.mock_event_seq,
        )
        self._ev_patch.start()
        self.addCleanup(self._ev_patch.stop)

    def tearDown(self):
        _clear_snowflake_generator_cache()
        super().tearDown()

    def test_init_with_valid_parameters(self, _mock_recount):
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        self.assertEqual(generator.datacenter_id, self.datacenter_id)
        self.assertEqual(generator.machine_id, self.machine_id)
        self.assertEqual(generator.start_timestamp, self.start_timestamp)
        self.assertEqual(generator.sequence, 0)
        self.assertEqual(generator.last_timestamp, -1)

    def test_init_with_invalid_datacenter_id(self, _mock_recount):
        with self.assertRaises(ValueError) as context:
            SnowflakeGenerator(
                datacenter_id=MASK_DATACENTER_ID + 1,
                machine_id=self.machine_id,
                start_timestamp=self.start_timestamp,
            )
        self.assertIn("datacenter_id", str(context.exception))

    def test_init_with_invalid_machine_id(self, _mock_recount):
        with self.assertRaises(ValueError) as context:
            SnowflakeGenerator(
                datacenter_id=self.datacenter_id,
                machine_id=MASK_MACHINE_ID + 1,
                start_timestamp=self.start_timestamp,
            )
        self.assertIn("machine_id", str(context.exception))

    def test_generate_single_id(self, _mock_recount):
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        id_value = generator.generate(self.business_id)
        self.assertGreater(id_value, 0)
        parsed = generator.parse_id(id_value)
        self.assertEqual(parsed["datacenter_id"], self.datacenter_id)
        self.assertEqual(parsed["machine_id"], self.machine_id)
        self.assertEqual(parsed["business_id"], self.business_id)
        self.assertGreaterEqual(parsed["timestamp"], self.start_timestamp)

    def test_generate_multiple_ids_are_unique(self, _mock_recount):
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        ids = generator.generate_batch(self.business_id, 10)
        self.assertEqual(len(ids), len(set(ids)))
        for id_value in ids:
            self.assertGreater(id_value, 0)

    def test_generate_batch(self, _mock_recount):
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        count = 5
        ids = generator.generate_batch(self.business_id, count)
        self.assertEqual(len(ids), count)
        for id_value in ids:
            parsed = generator.parse_id(id_value)
            self.assertEqual(parsed["datacenter_id"], self.datacenter_id)
            self.assertEqual(parsed["machine_id"], self.machine_id)
            self.assertEqual(parsed["business_id"], self.business_id)

    def test_parse_id(self, _mock_recount):
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        id_value = generator.generate(self.business_id)
        parsed = generator.parse_id(id_value)
        for key in ("timestamp", "datacenter_id", "machine_id", "recount", "business_id", "sequence"):
            self.assertIn(key, parsed)
        self.assertEqual(parsed["datacenter_id"], self.datacenter_id)
        self.assertEqual(parsed["machine_id"], self.machine_id)
        self.assertEqual(parsed["business_id"], self.business_id)

    def test_sequence_increment_within_same_millisecond(self, _mock_recount):
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        fixed_ts = self.start_timestamp + 1000
        with patch.object(generator, "_current_timestamp", return_value=fixed_ts):
            id1 = generator.generate(self.business_id)
            id2 = generator.generate(self.business_id)
        parsed1 = generator.parse_id(id1)
        parsed2 = generator.parse_id(id2)
        self.assertEqual(parsed1["timestamp"], parsed2["timestamp"])
        self.assertGreater(parsed2["sequence"], parsed1["sequence"])

    def test_restart_scenario_calls_recount_again(self, mock_recount):
        mock_recount.side_effect = [0, 1]
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        generator.generate(self.business_id)
        self.assertGreaterEqual(mock_recount.call_count, 2)

    def test_clock_backward_beyond_threshold(self, mock_recount):
        mock_recount.return_value = 0
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        generator.generate(self.business_id)
        original_ts = generator.last_timestamp
        backward_ts = original_ts - CLOCK_BACKWARD_THRESHOLD - 1
        mock_recount.reset_mock()
        self.mock_event_clock.reset_mock()
        self.mock_event_seq.reset_mock()
        with patch.object(generator, "_current_timestamp", return_value=backward_ts):
            generator.generate(self.business_id)
        self.mock_event_clock.assert_called()
        self.mock_event_seq.assert_not_called()
        mock_recount.assert_called()

    @patch.object(SnowflakeGenerator, "_wait_next_millis")
    def test_clock_backward_within_threshold(self, mock_wait, mock_recount):
        mock_recount.return_value = 0
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        generator.generate(self.business_id)
        original_ts = generator.last_timestamp
        backward_ts = original_ts - CLOCK_BACKWARD_THRESHOLD + 1
        recovered_ts = original_ts + 1
        mock_wait.return_value = recovered_ts
        with patch.object(generator, "_current_timestamp", return_value=backward_ts):
            id_value = generator.generate(self.business_id)
        self.assertGreater(id_value, 0)
        self.assertGreaterEqual(generator.last_timestamp, original_ts)

    def test_sequence_overflow_waits_next_millis(self, mock_recount):
        mock_recount.return_value = 0
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        generator.sequence = MASK_SEQUENCE
        fixed_ts = self.start_timestamp + 5000
        next_ts = fixed_ts + 1
        generator.last_timestamp = fixed_ts
        with patch.object(generator, "_current_timestamp", side_effect=[fixed_ts, next_ts]), patch.object(
            generator, "_wait_next_millis", return_value=next_ts
        ) as mock_wait:
            id_value = generator.generate(self.business_id)
        self.assertGreater(id_value, 0)
        mock_wait.assert_called_once()
        self.mock_event_seq.assert_called_once()
        self.assertEqual(generator.parse_id(id_value)["sequence"], 0)

    def test_concurrent_generation(self, mock_recount):
        mock_recount.return_value = 0
        generator = SnowflakeGenerator(
            datacenter_id=self.datacenter_id,
            machine_id=self.machine_id,
            start_timestamp=self.start_timestamp,
        )
        ids = []
        lock = threading.Lock()

        def generate_id():
            id_value = generator.generate(self.business_id)
            with lock:
                ids.append(id_value)

        threads = [threading.Thread(target=generate_id) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(ids), len(set(ids)))

    def test_different_datacenter_machine_ids(self, mock_recount):
        mock_recount.return_value = 0
        for dcid, mid, bid in (
            (0, 0, 0),
            (1, 1, 1),
            (MASK_DATACENTER_ID, MASK_MACHINE_ID, MASK_BUSINESS_ID),
        ):
            _clear_snowflake_generator_cache()
            generator = SnowflakeGenerator(
                datacenter_id=dcid,
                machine_id=mid,
                start_timestamp=self.start_timestamp,
            )
            id_value = generator.generate(bid)
            parsed = generator.parse_id(id_value)
            self.assertEqual(parsed["datacenter_id"], dcid)
            self.assertEqual(parsed["machine_id"], mid)
            self.assertEqual(parsed["business_id"], bid & MASK_BUSINESS_ID)
