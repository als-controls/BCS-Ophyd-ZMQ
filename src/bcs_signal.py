# Python Includes

import asyncio    # For handling asynchronous operations
import logging    # For logging errors
import threading  # For thread safety
import time       # For timestamps

# Bluesky Includes
from ophyd.signal import Signal

# BCS Includes
from bcs_server import BCSServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BCSSignal(Signal):

    """
    A custom Signal class for Bluesky that integrates with the BCS system via ZeroMQ.
    
    This class extends Ophyd's Signal class to communicate with hardware devices
    controlled by the Beamline Control System (BCS) through ZeroMQ.
    
    Parameters
    ----------
    *args
        Position arguments passed to the Signal constructor
    **kwargs
        Keyword arguments including:
        name : str
            Name of the signal (required)
        originalName : str
            Original name in Labview (with spaces, etc.)
        itemType : str
            Type of item ('ai' for analog input, 'motor' for motor)
        bridgeIP : str
            Host address of the BCS ZeroMQ server
        bridgePort : str or int
            Port number for the BCS ZeroMQ server
        units : str, optional
            Units for the signal values
    """

    def __init__(self, *args, **kwargs):

        logger.debug("Initializing BCSSignal...")
        
        # Extract name for the Signal base class
        name = kwargs.get("name", "unnamed_signal")
        
        # Initialize the base Signal class
        super().__init__(name=name)

        # Store the configuration
        self.name = name                                # example: "new_ai_2"
        self.originalName = kwargs.get("originalName")  # example: "New AI 2"
        self.itemType = kwargs.get("itemType", "unknown")
        self.host = kwargs.get("bridgeIP", "127.0.0.1")
        self.port = int(kwargs.get("bridgePort", 5577))
        self.units = kwargs.get("units", "")
        self.timeout = kwargs.get("timeout", 10000)  # Timeout in milliseconds

        # Initialize BCSServer instance for ZeroMQ communication
        self.bcs_server = BCSServer()
        
        # Track connection status
        self._connected = False
        
        # Thread safety lock for connection
        self._connection_lock = threading.Lock()
        
        logger.debug(f"BCSSignal initialized: {self.name}, type: {self.itemType}")

    async def ensure_connected(self):

        """Ensure that we have a connection to the BCS ZeroMQ server"""
        # Use a lock to prevent multiple connection attempts at the same time

        with self._connection_lock:
            if not self._connected:
                try:
                    logger.debug(f"Connecting to BCS server at {self.host}:{self.port}...")
                    await self.bcs_server.connect(self.host, self.port)
                    self._connected = True
                    logger.debug("Connected to BCS server")
                except Exception as e:
                    logger.error(f"Error connecting to BCS ZeroMQ server: {e}")
                    raise ConnectionError(f"Failed to connect to BCS server: {e}")

    def __str__(self):

        """String representation of the signal for better debugging"""
        content = ""
        content += f" name         : {self.name}\n"
        content += f" originalName : {self.originalName}\n"
        content += f" itemType     : {self.itemType}\n"
        content += f" host         : {self.host}\n"
        content += f" port         : {self.port}\n"
        content += f" units        : {self.units}\n"
        content += f" connected    : {self._connected}\n"

        # Define the bounding box
        border = "=" * 40
        box = f"{border}\n"
        box += f"=         BCSSignal Object         =\n"
        box += f"{border}\n"
        box += content
        box += border

        return box

    async def get(self):

        """
        Get the current value of the signal asynchronously
        
        Returns
        -------
        float or int
            The current value of the signal
        
        Raises
        ------
        RuntimeError
            If there's an error in the ZeroMQ communication
        ValueError
            If the requested item is not found or no data is returned
        """

        # Ensure we're connected to the BCS server
        await self.ensure_connected()

        try:
            # Handle different item types
            if self.itemType == "ai":
                # Get analog input value
                response = await self.bcs_server.get_freerun([self.originalName])
                
                # Validate response
                if not response.get('success', False):
                    error_msg = response.get('error_description', 'Unknown error')
                    raise RuntimeError(f"Failed to get AI data: {error_msg}")
                
                # Check for not found
                if 'not_found' in response and response['not_found']:
                    raise ValueError(f"AI channel not found: {self.originalName}")
                    
                # Extract the value
                if 'data' in response and len(response['data']) > 0:
                    return response['data'][0]
                else:
                    raise ValueError(f"No data returned for AI: {self.originalName}")
            
            elif self.itemType == "motor":
                # Get motor position
                response = await self.bcs_server.get_motor([self.originalName])
                
                # Validate response
                if not response.get('success', False):
                    error_msg = response.get('error_description', 'Unknown error')
                    raise RuntimeError(f"Failed to get motor data: {error_msg}")
                
                # Check for not found
                if 'not_found' in response and response['not_found']:
                    raise ValueError(f"Motor not found: {self.originalName}")
                    
                # Extract position
                if 'data' in response and len(response['data']) > 0:
                    motor_data = response['data'][0]
                    return motor_data.get('position', 0)
                else:
                    raise ValueError(f"No data returned for motor: {self.originalName}")
            
            else:
                raise ValueError(f"Unsupported item type: {self.itemType}")
                
        except Exception as e:
            logger.error(f"Error in get() for {self.name}: {e}")
            raise

    async def put(self, value):

        """
        Set the value of the signal asynchronously
        
        Parameters
        ----------
        value : float or int
            The value to set
            
        Raises
        ------
        NotImplementedError
            If setting values is not supported for this signal type
        ValueError
            If the item type is not supported
        """

        return await self.set(value)  # Delegate to set method for compatibility

    async def set(self, value):

        """
        Set the value of the signal asynchronously
        
        Parameters
        ----------
        value : float or int
            The value to set
            
        Returns
        -------
        dict
            The response from the server
            
        Raises
        ------
        NotImplementedError
            If setting values is not supported for this signal type
        ValueError
            If the item type is not supported
        """

        logger.info(f"Setting {self.name} ({self.itemType}) to {value}...")
        
        # Ensure we're connected to the BCS server
        await self.ensure_connected()
        
        try:
            # Handle setting values based on item type
            if self.itemType == "motor":
                # Move the motor to the specified position
                response = await self.bcs_server.move_motor([self.originalName], [float(value)])
                
                # Check if the request was successful
                if not response.get('success', False):
                    error_msg = response.get('error_description', 'Unknown error')
                    raise RuntimeError(f"Failed to move motor: {error_msg}")
                
                # Check if any motors were not found
                if 'not_found' in response and len(response['not_found']) > 0:
                    raise ValueError(f"Motor not found: {self.originalName}")
                    
                # Check if any motors timed out
                if 'timed_out' in response and len(response['timed_out']) > 0:
                    raise TimeoutError(f"Motor move timed out: {self.originalName}")
                    
                logger.info(f"Motor {self.originalName} successfully commanded to move to {value}")
                return response
                
            elif self.itemType == "ai":
                # Analog inputs typically can't be set
                raise NotImplementedError(f"Setting values for AI channels is not supported: {self.originalName}")
                
            else:
                raise ValueError(f"Unsupported item type for setting values: {self.itemType}")
                
        except Exception as e:
            logger.error(f"Error in set() for {self.name}: {e}")
            raise

    async def read(self):

        """
        Read the current value and timestamp for Bluesky integration
        
        Returns
        -------
        dict
            A dictionary with the signal name as key, containing the value and timestamp
        """

        try:
            # Get the current value
            value = await self.get()
            
            # Generate a timestamp
            timestamp = time.time()
            
            # Return in the format expected by Bluesky
            return {self.name: {"value": value, "timestamp": timestamp}}
            
        except Exception as e:
            logger.error(f"Error in read() for {self.name}: {e}")
            raise

    def getPrefix(self):

        """
        Get the prefix for the signal
        
        Returns
        -------
        str
            The prefix string
        """
        if hasattr(self, 'ophyd_item'):
            return self.ophyd_item['prefix']
        return ""

    # Thread-safe wrapper methods for synchronous code
    def get_sync(self):

        """Synchronous wrapper for get()"""
        loop = asyncio.new_event_loop()
        
        try:
            return loop.run_until_complete(self.get())
        finally:
            loop.close()

    def set_sync(self, value):

        """Synchronous wrapper for set()"""
        loop = asyncio.new_event_loop()

        try:
            return loop.run_until_complete(self.set(value))
        finally:
            loop.close()

    def read_sync(self):

        """Synchronous wrapper for read()"""
        loop = asyncio.new_event_loop()

        try:
            return loop.run_until_complete(self.read())
        finally:
            loop.close()
