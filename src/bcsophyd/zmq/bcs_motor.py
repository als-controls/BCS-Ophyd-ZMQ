# Python Includes
import asyncio
import threading
import time
from datetime import datetime
from threading import Thread

from loguru import logger

# Ophyd Includes
from ophyd import Device
from ophyd import PositionerBase
from ophyd.status import Status

# BCS Includes
from .bcs_server import BCSServer

# A custom motor class for Bluesky that integrates with the BCS system via ZeroMQ.
# It extends the Ophyd Device and PositionerBase classes, enabling seamless integration
# into the Bluesky framework for motor control and scanning workflows.
class BCSMotor(Device, PositionerBase): 

    # Constructor
    def __init__(self, *args, **kwargs):
        logger.debug("BCSMotor - __init__() - Start.")

        # Initialize the parent classes
        # The super() call ensures that the parent classes (Device and PositionerBase)
        # are properly initialized, setting up core functionality for the motor device.
        # The `name` parameter identifies the motor within the Bluesky framework.
        super().__init__(name=kwargs["name"])

        # Initialize attributes specific to BCSMotor
        self.name         = kwargs["name"]          # example: "motor_2"
        self.originalName = kwargs["originalName"]  # example: "Motor 2"
        self.itemType     = kwargs["itemType"]
        self.prefix       = kwargs["prefix"]
        self.units        = kwargs["units"]

        # For ZeroMQ server connection
        logger.debug(f"bridgeIP: {kwargs['bridgeIP']}")
        logger.debug(f"bridgePort: {kwargs['bridgePort']}")

        self.host         = kwargs["bridgeIP"]
        self.port         = int(kwargs["bridgePort"])

        # Create ZeroMQ client for motor communication
        self.bcs_server = BCSServer()
        self._connected = False

        # Motor configuration and initial state
        self._position    = 0
        self.velocity     = 0
        self.acceleration = 0

        # Motor timing parameters (required by PositionerBase)
        self.timeout      = kwargs.get("timeout", 60.0)      # Default 60 second timeout
        self.settle_time  = kwargs.get("settle_time", 0.0)   # Default no settle time

        # Motor status flags
        self.isMoving     = False
        self.moveComplete = True

        # Use a lock to prevent concurrent access to the ZeroMQ server
        self._lock = threading.Lock()

        logger.debug("BCSMotor - __init__() - End.")

    # Ensure connection to the ZeroMQ server
    async def _ensure_connected(self):
        """Ensure connection to the ZeroMQ server before making requests"""
        if not self._connected:
            logger.debug(f"BCSMotor - Connecting to ZeroMQ server at {self.host}:{self.port}")
            await self.bcs_server.connect(self.host, self.port)
            self._connected = True
            logger.debug(f"BCSMotor - Connected to ZeroMQ server at {self.host}:{self.port}")

    # Overload print behavior for better debugging
    def __str__(self):

        # Create the content to display
        content = ""
        content += f" name        : {self.name}         \n"
        content += f" prefix      : {self.prefix}       \n"
        content += f" itemType    : {self.itemType}     \n"
        content += f" timeout     : {self.timeout}      \n"        
        content += f" settle_time : {self.settle_time}  \n"
        content += f" host        : {self.host}         \n"
        content += f" port        : {self.port}         \n"
        content += f" position    : {self._position}     \n"        
        content += f" velocity    : {self.velocity}     \n" 
        content += f" acceleration: {self.acceleration} \n"         
        
        # Define the bounding box
        border = "=" * 32
        box = f"{border}\n"  # Top border
        box += f"=       BCSMotor Object        =\n"  # Title
        box += f"{border}\n"  # Title border
        box += content  # Add content
        box += border  # Bottom border

        return box

    # Provide metadata for the motor's readable signal
    def describe(self):

        # Create a temporary dictionary to store the description
        tempDescription = {

            self.name: {
                "source": "BCSMotor",
                "dtype" : "number",
                "shape" : [],
                "units" : self.units
            }

        }

        logger.debug(f"Motor description: {tempDescription}")

        return tempDescription

    # Synchronous method to get the motor position - useful for testing
    def get(self):
        """
        Synchronous method to get the motor position.
        This provides a simpler interface for basic testing.

        Returns:
            float: The current position of the motor
        """
        logger.debug(f"BCSMotor - get() - Returning current position: {self._position}")
        return self._position

    def move(self, new_position, wait=True, timeout=None):
        """
        Moves the motor to the specified new position and monitors the progress.

        :param new_position: Target position for the motor.
        :param wait: If True, blocks until the motor finishes moving.
        :param timeout: Maximum time to wait for the move to complete.
        """
        logger.debug("BCSMotor - move() - Start")

        # Set motor to moving state
        self.moveComplete = False
        self.isMoving     = True

        # Start the motor movement
        logger.debug(f"BCSMotor - move() - Calling zmq_move_motor({self.originalName}, {new_position})")
        self.zmq_move_motor([self.originalName], [new_position])

        # Initialize an Ophyd.Status object to track the move progress
        # self.monitor_motor_status receives a status object
        # to update when move is done.
        logger.debug("BCSMotor - move() - Creating Ophyd Status Object to Track Move.")
        status = Status()

        # Start a thread to monitor the motor status
        monitor_thread_instance = threading.Thread(
            target=self.monitor_motor_status, args=(new_position, status, timeout), daemon=True
        )

        monitor_thread_instance.start()

        # Wait for the monitoring thread to finish if wait=True
        if wait:
            logger.debug("BCSMotor - move() - Waiting for monitor_motor_status to check if motor reached target position.")
            monitor_thread_instance.join(timeout)

        logger.debug("BCSMotor - move() - End.")

        return status

    def monitor_motor_status(self, target_position, status, timeout=None, check_interval=0.1):
        """
        Monitors the motor's internal attributes periodically to determine when the move is complete.

        Args:
            target_position (float): The target position of the motor.
            status (Status): The Status object to update when the move is complete.
            timeout (float): Maximum time (in seconds) to wait for the move to complete.
            check_interval (float): Time interval (in seconds) between status checks.
        """
        logger.debug("BCSMotor - monitor_motor_status() - Start.")

        start_time = time.time()

        try:
            while True:
                logger.trace("BCSMotor - monitor_motor_status() - Checking status...")

                # Check for timeout
                elapsed_time = time.time() - start_time

                if timeout and elapsed_time > timeout:
                    logger.warning("BCSMotor - monitor_motor_status() - Timeout.")
                    status.set_exception(TimeoutError("BCSMotor - monitor_motor_status() - Timeout."))
                    break

                # Update the motor's internal state
                self.update()

                diff = abs(self._position - target_position)

                logger.trace(f"BCSMotor - monitor_motor_status() - Current Position: {self._position}, Target: {target_position}, Move Complete: {self.moveComplete}, Diff: {diff}")

                # Check if the motor has reached the target position and stopped moving
                if self.moveComplete:
                    logger.debug("BCSMotor - monitor_motor_status() - Move Complete.")
                    status.set_finished()
                    break

                # Wait before checking again
                time.sleep(check_interval)

        except Exception as e:
            logger.error(f"BCSMotor - monitor_motor_status() - Error: {e}")
            status.set_exception(e)

        logger.debug("BCSMotor - monitor_motor_status() - End.")

    @property
    def position(self):
        logger.trace("=== position() ===")
        return self._position

    # Return the converted motor position as an Ophyd Signal
    async def read(self):
        logger.debug("BCSMotor - read() - Start.")
        logger.debug("BCSMotor - read() - Calling self.zmq_get_motor_full_async(self.originalName)")

        # Query the full motor information, including the position
        # Use the async version of the method to avoid the name collision
        queryResult = await self.zmq_get_motor_full_async(self.originalName)

        logger.debug("BCSMotor - read() - Query Results Received.")

        # Generate a timestamp
        timestamp = datetime.now().isoformat()  # ISO 8601 format for compatibility

        logger.debug("BCSMotor - read() - Reading Raw Motor Position.")
        
        # Extract the converted motor position
        converted_motor_position = queryResult[0]['Raw Motor Position']

        # Updates internal position
        self._position = converted_motor_position
        
        logger.debug(f"BCSMotor - read() - Raw Motor Position: {round(self._position, 3)}.")

        # Ophyd Signal
        tempSignal = {
            self.name: {
                "value": self._position,
                "timestamp": timestamp
            }
        }

        logger.debug("BCSMotor - read() - End...")

        return tempSignal

    # Intention to move the motor to the given position
    def set(self, position):
        logger.debug(f"BCSMotor - set({position}) - Now we call move()...")
        logger.debug(f"BCSMotor - move({position}) - Calling it...")        
        return self.move(position, wait=True)
    
    def stop(self, *, success=False):
        name = self.originalName
        
        logger.debug(f"BCSMotor - stop({name}) - Start")

        self.zmq_stop_motor([self.originalName])

        """Simulate stopping the motor."""
        self.isMoving = False

        logger.debug(f"BCSMotor - stop({name}) - End")
    
    # Updates the internal attributes of the motor by querying the current motor status
    # from the ZeroMQ endpoint and parsing it.
    def update(self):

        logger.trace("BCSMotor - update() - start...")

        try:
            # Query the motor's full data
            logger.trace("BCSMotor - update() - Calling self.zmq_get_motor_full")
            list_result = self.zmq_get_motor_full(self.originalName)

            # The query returns a list with a single element
            # We extract this dictionary below:
            fullDictionary = list_result[0]

            # Parsing 
            motorState = fullDictionary.get('Motor State', {})
            
            # Updating Values
            self.moveComplete = motorState.get('Move Complete', False)
            self._position = fullDictionary.get('Raw Motor Position', self._position)
            
        except Exception as e:
            logger.error(f"update() - Error: {e}")

    ###########################
    ###   ZeroMQ Wrappers   ###
    ###########################

    # Async method for getting motor data - this is the method that read() should use
    async def zmq_get_motor_full_async(self, motor_name):

        """
        Get detailed motor information directly via ZeroMQ (async version)
        
        Args:
            motor_name (str): Name of the motor to query
            
        Returns:
            list: List of motor data dictionaries
        """

        logger.debug(f"BCSMotor - zmq_get_motor_full_async({motor_name}) - Start.")
        
        # Ensure we have a connection to the server
        await self._ensure_connected()
        
        # Call the BCS server to get motor data
        response = await self.bcs_server.get_motor_full([motor_name])
        
        # Check for success
        if not response.get('success', False):
            error_desc = response.get('error_description', 'Unknown error')
            raise RuntimeError(f"Failed to get motor data: {error_desc}")
            
        # Parse the response
        motor_data = self.parse_get_motor_full(response)
        
        logger.debug(f"BCSMotor - zmq_get_motor_full_async({motor_name}) - End.")
        return motor_data

    # Thread-safe wrapper for getting motor information
    def zmq_get_motor_full(self, motor_name):
        
        """Thread-safe wrapper for getting motor information (sync version)"""
        logger.debug(f"BCSMotor - zmq_get_motor_full({motor_name}) (Thread wrapper) - Start.")

        # Use a mutable container to store the result from the asynchronous operation
        result_container = {}

        # Define a function to execute the asynchronous operation in a new thread
        def runInThread():
            # Use asyncio.run to run the coroutine in a new event loop
            result_container['queryMotorFull'] = asyncio.run(self._zmq_get_motor_full_async(motor_name))

        # Create a new thread to run the asynchronous operation
        thread = Thread(target=runInThread)
        thread.start()
        thread.join()

        # Retrieve the result
        motorFullData = result_container.get('queryMotorFull')
        if not motorFullData:
            raise RuntimeError(f"Failed to get motor data for {motor_name}")
            
        logger.debug(f"BCSMotor - zmq_get_motor_full({motor_name}) (Thread wrapper) - End.")
        return motorFullData
        
    # Internal async method for getting motor data
    async def _zmq_get_motor_full_async(self, motor_name):
        """Internal async method for getting motor data"""
        await self._ensure_connected()
        response = await self.bcs_server.get_motor_full([motor_name])
        return self.parse_get_motor_full(response)

    # Thread-safe method to move motor using ZeroMQ
    def zmq_move_motor(self, motors, goals):
        """Thread-safe method to move motors using ZeroMQ"""
        logger.debug(f"BCSMotor - zmq_move_motor({motors[0]}, {goals[0]}) - Start.")

        # Define a function to execute the asynchronous operation in a new thread
        def runInThread():
            asyncio.run(self._zmq_move_motor_async(motors, goals))

        # Create a new thread
        thread = Thread(target=runInThread)
        thread.start()
        thread.join()

        logger.debug(f"BCSMotor - zmq_move_motor({motors[0]}, {goals[0]}) - End.")
        
    # Internal async method for moving motors
    async def _zmq_move_motor_async(self, motors, goals):
        """Internal async method for moving motors"""
        await self._ensure_connected()
        response = await self.bcs_server.move_motor(motors, goals)
        
        if not response.get('success', False):
            error_desc = response.get('error_description', 'Unknown error')
            raise RuntimeError(f"Failed to move motor: {error_desc}")
            
        # Check for motors not found
        if 'not_found' in response and response['not_found']:
            raise ValueError(f"Motors not found: {response['not_found']}")
            
        # Check for timed out motors
        if 'timed_out' in response and response['timed_out']:
            raise TimeoutError(f"Motors timed out: {response['timed_out']}")

    # Thread-safe method to stop motor using ZeroMQ
    def zmq_stop_motor(self, motors):
        """Thread-safe method to stop motors using ZeroMQ"""
        motors_str = ", ".join(motors)
        logger.debug(f"BCSMotor - zmq_stop_motor([{motors_str}]) - Start.")

        # Define a function to execute the asynchronous operation in a new thread
        def runInThread():
            asyncio.run(self._zmq_stop_motor_async(motors))

        # Create a new thread
        thread = Thread(target=runInThread)
        thread.start()
        thread.join()

        logger.debug(f"BCSMotor - zmq_stop_motor([{motors_str}]) - End.")
        
    # Internal async method for stopping motors
    async def _zmq_stop_motor_async(self, motors):
        """Internal async method for stopping motors"""
        await self._ensure_connected()
        response = await self.bcs_server.stop_motor(motors)
        
        if not response.get('success', False):
            error_desc = response.get('error_description', 'Unknown error')
            raise RuntimeError(f"Failed to stop motor: {error_desc}")

    #############################
    ###   Parsing Functions   ###
    #############################

    # Parses the response of the `get_motor_full` ZeroMQ call
    def parse_get_motor_full(self, input_data):
        """Parse the motor data response from ZeroMQ"""
        logger.debug("BCSMotor - parse_get_motor_full() - Start.")

        # Check if 'success' is True
        if not input_data.get('success', False):
            raise ValueError(f"Operation not successful: {input_data.get('error_description', 'Unknown error')}")

        # Extract the 'data' dictionary
        data = input_data.get('data', None)
        if not data:
            raise ValueError("No data found in the response.")
        
        logger.debug("BCSMotor - parse_get_motor_full() - End.")

        return data
