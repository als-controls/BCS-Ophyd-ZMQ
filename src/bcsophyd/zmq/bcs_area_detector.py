import threading
import time

from loguru import logger
from ophyd import Component as Cpt
from ophyd import Device, Component, Signal
from ophyd.device import Kind
from ophyd.signal import Signal, SignalRO
from ophyd.status import DeviceStatus

class BCSAreaDetector(Device):

    # Basic signals
    acquire = Component(Signal, value=0)
    image = Component(Signal, value=[[1,2,3], [4,5,6], [7,8,9]])
    total_intensity = Component(Signal, value=0.0)


    def __init__(self, *args, **kwargs): #NormalScan #FlyingScan

        """Initialize detector with simple 3x3 static patterns"""
        logger.debug("BCSAreaDetector - __init__")

        super().__init__(*args, **kwargs)

        self._flying = False
        self._staged = False

        # Simple 3x3 patterns for testing
        self._patterns = [
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            [[9, 8, 7], [6, 5, 4], [3, 2, 1]],
            [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
        ]
        
        self._pattern_idx = 0

        # Set the default subscription type
        self._default_sub = self.SUB_VALUE

    def acquire_frame(self, status): #NormalScan

        """Acquire a single frame and update status"""
        logger.debug("BCSAreaDetector - acquire_frame()")
        # Get current pattern
        pattern = self._patterns[self._pattern_idx % len(self._patterns)]
        self._pattern_idx += 1
        
        # Set image and calculate total intensity
        self.image.put(pattern)
        total = sum(sum(row) for row in pattern)
        self.total_intensity.put(total)
        
        # Mark acquisition as complete
        status._finished()

    def collect(self): #NotInNormalScan #FlyingScan

        """
        Collect data points during fly scan.
        Yields dictionaries containing data and metadata.
        """

        logger.debug("BCSAreaDetector - collect()")

        if not self._flying:
            return
            
        for pattern in self._patterns:

            self.image.put(pattern)

            total = sum(sum(row) for row in pattern)

            self.total_intensity.put(total)
            
            yield {
                'data': {'total_intensity': total},
                'timestamps': {'total_intensity': time.time()},
                'time': time.time(),
                'data_key': 'primary'
            }
            time.sleep(0.1)

    def complete(self): #NotInNormalScan #FlyingScan

        """End flying mode and return status"""
        logger.debug("BCSAreaDetector - complete()")
        if not self._flying:
            raise RuntimeError("Device is not flying")
            
        self._flying = False
        status = DeviceStatus(self)
        status._finished()
        return status

    def describe(self): #NormalScan

        """
        Describe the detector's data structure for normal scans.
        Returns metadata about the detector's signals.
        """

        logger.debug("BCSAreaDetector - describe()")

        return {
            f'{self.name}_image': {
                'source': 'BCSAreaDetector',
                'dtype': 'array',
                'shape': [3, 3]
            },
            f'{self.name}_total_intensity': {
                'source': 'BCSAreaDetector',
                'dtype': 'number',
                'shape': []
            }
        }

    def describe_collect(self): #NormalScan #FlyingScan

        """
        Describe the data structure for fly scans.
        Returns metadata about the collected data.
        """
        logger.debug("BCSAreaDetector - describe_collect()")

        return {
            'primary': {
                f'{self.name}_total_intensity': {
                    'source': 'BCSAreaDetector',
                    'dtype': 'number',
                    'shape': []
                }
            }
        }

    def kickoff(self): #NotInNormal #Just in Flying Scan

        """
        Start flying mode. Auto-stages if needed.
        Returns status object.
        """

        logger.debug("BCSAreaDetector - kickoff()")
        if not self._staged:
            self.stage()
            
        self._flying = True
        self._pattern_idx = 0
        status = DeviceStatus(self)
        status._finished()
        return status

    def read(self): #NormalScan

        """
        Read current values for normal scans.
        Returns dictionary with current values and timestamps.
        """
        logger.debug("BCSAreaDetector - read()")
        return {
            f'{self.name}_image': {
                'value': self.image.get(),
                'timestamp': time.time()
            },
            f'{self.name}_total_intensity': {
                'value': self.total_intensity.get(),
                'timestamp': time.time()
            }
        }

    def stage(self): #NormalScan

        """
        Prepare detector for scanning.
        Returns list containing self.
        """

        logger.debug("BCSAreaDetector - stage()")

        if self._staged:
            return [self]
        
        self._staged = True
        self._pattern_idx = 0
        self.acquire.put(0)

        return [self]

    @property
    def SUB_VALUE(self):
        """Subscription type for value updates"""
        return 'value'

    def subscribe(self, callback, event_type=None, **kwargs):
        """Subscribe to detector events"""
        if event_type is None:
            event_type = self.SUB_VALUE
        # Change this line to subscribe to total_intensity signal
        return self.total_intensity.subscribe(callback, event_type=event_type, **kwargs)

    def trigger(self): #NormalScan

        """
        Trigger a single acquisition.
        Returns status object.
        """

        logger.debug("BCSAreaDetector - trigger()")

        if not self._staged:
            raise RuntimeError("Device must be staged before triggering")
            
        status = DeviceStatus(self)
        
        # Simulate acquisition in separate thread
        
        thread = threading.Thread(target=lambda: self.acquire_frame(status))
        thread.start()
        
        return status

    def unstage(self): #NormalScan

        """
        Clean up after scanning.
        Returns list containing self.
        """

        logger.debug("BCSAreaDetector - unstage()")

        if not self._staged:
            return [self]
        
        self._staged = False
        self.acquire.put(0)
        
        return [self]