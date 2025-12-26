"""Snowflake ID generation service"""

import threading
import time
from typing import List

from app_snowflake.consts.snowflake_const import MASK_DATACENTER_ID, MASK_MACHINE_ID, MASK_BUSINESS_ID, \
    MASK_SEQUENCE, TIMESTAMP_SHIFT, DATACENTER_SHIFT, MACHINE_SHIFT, RECOUNT_SHIFT, BUSINESS_SHIFT, DATACENTER_BITS, \
    MACHINE_BITS, RECOUNT_BITS, BUSINESS_BITS, CLOCK_BACKWARD_THRESHOLD
from app_snowflake.services.recounter_service import create_or_update_recount


class SnowflakeGenerator:
    """Snowflake ID generator
    
    Bit allocation (64 bits total):
    - 1 bit: Sign bit (always 0)
    - 2 bits: Datacenter ID (0-3)
    - 3 bits: Machine ID (0-7)
    - 2 bits: Restart/Clock backward counter (0-3)
    - 3 bits: Business ID (0-7)
    - 41 bits: Timestamp (milliseconds)
    - 12 bits: Sequence number (0-4095)
    """

    def __init__(self,
                 datacenter_id: int,
                 machine_id: int,
                 start_timestamp: int):
        """
        Initialize Snowflake generator
        
        Args:
            datacenter_id: Datacenter ID (0-3)
            machine_id: Machine ID (0-7)
            start_timestamp: Start timestamp in milliseconds
        """
        # lazy load
        from app_snowflake.services.event_service import rec_service_start

        # Parameter validation
        if datacenter_id > MASK_DATACENTER_ID or datacenter_id < 0:
            raise ValueError(
                f"datacenter_id must be between 0 and {MASK_DATACENTER_ID}, got {datacenter_id}"
            )
        if machine_id > MASK_MACHINE_ID or machine_id < 0:
            raise ValueError(
                f"machine_id must be between 0 and {MASK_MACHINE_ID}, got {machine_id}"
            )

        self.datacenter_id = datacenter_id
        self.machine_id = machine_id
        self.start_timestamp = start_timestamp

        self.recount = create_or_update_recount(self.datacenter_id, self.machine_id)
        self.last_timestamp = self._current_timestamp()
        self.sequence = 0

        self.lock = threading.Lock()

        rec_service_start(self.datacenter_id, self.machine_id, "", {"recount": self.recount})

    def generate(self, business_id: int) -> int:
        """
        Generate a single ID

        Args:
            business_id: Business ID (0-7)

        Returns:
            Generated 64-bit ID

        Raises:
            ClockBackwardException: Clock backward exception
        """
        # lazy load
        from app_snowflake.services.event_service import rec_clock_backward, rec_sequence_overflow

        business_id = business_id & MASK_BUSINESS_ID  # ensure business_id is within bounds

        with self.lock:
            timestamp = self._current_timestamp()

            # clock backward detection
            if timestamp < self.last_timestamp:
                offset = self.last_timestamp - timestamp
                if offset <= CLOCK_BACKWARD_THRESHOLD:
                    # within tolerance, wait for clock recovery
                    timestamp = self._wait_next_millis(self.last_timestamp)
                else:
                    # clock backward
                    # todo: put self.last_timestamp into a MAX_RECOUNT-length queue
                    #       the queue also holds MAX_RECOUNT max last_timestamps
                    #       if self.last_timestamp is greater than the corresponding max last_timestamp, recount
                    #       else, throw ClockBackwardException directly
                    self.recount = create_or_update_recount(self.datacenter_id, self.machine_id)
                    rec_clock_backward(self.datacenter_id, self.machine_id, "", {"recount": self.recount})
            elif timestamp == self.last_timestamp:
                # within the same millisecond
                self.sequence = (self.sequence + 1) & MASK_SEQUENCE
                # sequence overflow
                if self.sequence == 0:
                    timestamp = self._wait_next_millis(self.last_timestamp)
                    rec_sequence_overflow(self.datacenter_id, self.machine_id)
            else:
                # new millisecond, reset sequence
                self.sequence = 0

            self.last_timestamp = timestamp

            # Assemble ID
            return ((timestamp - self.start_timestamp) << TIMESTAMP_SHIFT) | \
                (self.datacenter_id << DATACENTER_SHIFT) | \
                (self.machine_id << MACHINE_SHIFT) | \
                (self.recount << RECOUNT_SHIFT) | \
                (business_id << BUSINESS_SHIFT) | \
                self.sequence

    def generate_batch(self, business_id: int, count: int) -> List[int]:
        """
        Generate IDs in batch

        Args:
            business_id: Business ID (0-7)
            count: Number of IDs to generate

        Returns:
            List of IDs
        """
        return [self.generate(business_id) for _ in range(count)]

    def parse_id(self, id_value: int) -> dict:
        """
        Parse ID to extract detailed information

        Args:
            id_value: ID to parse

        Returns:
            Dictionary containing timestamp, datacenter_id, machine_id,
            recount, business_id, and sequence
        """
        timestamp = (id_value >> TIMESTAMP_SHIFT) + self.start_timestamp
        datacenter_id = (id_value >> DATACENTER_SHIFT) & ((1 << DATACENTER_BITS) - 1)
        machine_id = (id_value >> MACHINE_SHIFT) & ((1 << MACHINE_BITS) - 1)
        recount = (id_value >> RECOUNT_SHIFT) & ((1 << RECOUNT_BITS) - 1)
        business_id = (id_value >> BUSINESS_SHIFT) & ((1 << BUSINESS_BITS) - 1)
        sequence = id_value & MASK_SEQUENCE

        return {
            "datacenter_id": datacenter_id,
            "machine_id": machine_id,
            "recount": recount,
            "business_id": business_id,
            "timestamp": timestamp,
            "sequence": sequence
        }

    def _current_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)

    def _wait_next_millis(self, till_timestamp: int) -> int:
        """Wait until next millisecond"""
        current_timestamp = self._current_timestamp()
        wait = till_timestamp - current_timestamp
        if wait <= 0:
            return current_timestamp
        time.sleep((wait + 1) / 1000)  # sleep slightly longer to ensure current_timestamp > till_timestamp
        return self._current_timestamp()