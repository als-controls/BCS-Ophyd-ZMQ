# Python Includes
import asyncio
import json
import os
import re
import sys
import time

from loguru import logger

# Happi client for managing device metadata
from happi import Client, OphydItem
import zmq
import zmq.asyncio

# BCS Includes
from .bcs_server import BCSServer

# A class to manage the Happi client 
# and populate it with devices (e.g., motors and analog inputs)
# from a JSON configuration retrieved directly from the BCS server via ZeroMQ 
class BCSDeviceManager:
    
    # Constructor - synchrounous, only initializes variables
    def __init__(self, host="127.0.0.1", port=5577, timeout_ms=5000):
        # Host address - Default: 127.0.0.1
        self.host = host
        
        # ZeroMQ port - Default: 5577
        self.port = port
        
        # Timeout in milliseconds
        self.timeout_ms = timeout_ms

        # Initialize BCS server instance
        self.bcs_server = BCSServer()

        # Path to the Happi database file
        self.db_path = "happi_epics_db.json"
        
        # Flag to track whether we're connected
        self._connected = False
        
        # Initialize the Happi client (this is synchronous)
        self.client = self.create_client()

        # Device names that have been seen
        self.seen_names = dict()
    
    # Async method to connect to server and populate data
    async def connect(self):
        """Connect to the BCS server and populate the device database"""
        if self._connected:
            return True
            
        # Check connection
        if not await self.check_server_connection_async():
            return False
            
        # Populate the Happi client
        try:
            # Connect to server and populate database
            await self.populate_client_from_config_async()
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.info("Possible solutions:")
            logger.info("- Check if BCS ZeroMQ server is running...")
            logger.info(f"- Check if you can connect to ZeroMQ at {self.host}:{self.port}")
            logger.info("- Check if Labview is running on the BCS server machine...")
            logger.info(f"- Check if you can ping {self.host}")
            logger.info("- Check your connectivity...")
            return False
    
    # Creates and initializes a Happi client, managing the device database.
    def create_client(self):
        # Check if the file exists and delete it
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.debug(f"Existing file '{self.db_path}' has been deleted.")

        # Initialize the client
        client = Client(path=self.db_path)
        logger.debug(f"Happi client initialized with database: {self.db_path}")

        return client

    # Asynchrounous check if we can connect to the server
    async def check_server_connection_async(self):
        """Check if the BCS ZeroMQ server is accessible asynchronously"""
        logger.info(f"Testing connection to BCS server at {self.host}:{self.port}...")

        # Create a simple ZeroMQ REQ socket to test connection
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.REQ)

        # Set timeout to prevent hanging
        socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)

        try:
            # Connect to the server
            logger.debug("socket.connect")
            socket.connect(f'tcp://{self.host}:{self.port}')

            # Try to send the 'public' request (this is what BCSServer does internally)
            logger.debug("socket.send (public)")
            await socket.send(b'public')

            # Wait for a response
            response = await socket.recv()

            if response:
                logger.success(f"Successfully connected to BCS server at {self.host}:{self.port}")
                return True

        except zmq.error.Again:
            # Timeout occurred - no response from server
            logger.error(f"No response from BCS server at {self.host}:{self.port} (timeout after {self.timeout_ms/1000} seconds)")
            logger.info("The server may be down or unreachable. Please check your connection and try again.")
            return False

        except Exception as e:
            # Other connection errors
            logger.error(f"Failed to connect to BCS server at {self.host}:{self.port}")
            logger.error(f"Error details: {str(e)}")
            return False

        finally:
            # Clean up resources
            socket.close(linger=0)

        return False

    # Synchronous version of check_server_connection for backward compatibility
    def check_server_connection(self):
        """Synchronous wrapper for check_server_connection_async"""
        try:
            # Create a new event loop for this function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async check in the new event loop
            result = loop.run_until_complete(self.check_server_connection_async())
            
            # Clean up
            loop.close()
            
            if not result:
                sys.exit(1)
                
            return result
        finally:
            # Ensure we restore the event loop
            asyncio.set_event_loop(None)

    # Initialize connection to BCS ZeroMQ server
    async def connect_to_bcs_server(self):
        """Connect to the BCS ZeroMQ server"""
        try:
            # Connect to the ZeroMQ server using the existing instance
            logger.info(f"Establishing secure connection to BCS server at {self.host}:{self.port}...")
            await self.bcs_server.connect(self.host, self.port)
            logger.success(f"Connected to BCS ZeroMQ server at {self.host}:{self.port}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to BCS ZeroMQ server: {e}")
            raise ValueError(f"Connection to BCS server failed: {e}")

    # Asynchronous version of populate_client_from_config
    async def populate_client_from_config_async(self):
        """Populate the Happi client from configuration data asynchronously"""
        try:
            # Connect to BCS server
            await self.connect_to_bcs_server()

            # Get configuration data using BCSServer
            logger.info("Retrieving device configuration from BCS server...")
            config_response = await self.bcs_server.get_bcsconfiguration()

            if not config_response or not config_response.get("success", False):
                error_msg = config_response.get("error_description", "Unknown error") if config_response else "No response"
                raise RuntimeError(f"Failed to retrieve configuration data: {error_msg}")

            logger.success("Retrieved configuration from BCS server")

            # Parse the configuration from the response
            config_data = {}
            if "configuration" in config_response:
                try:
                    config_data = json.loads(config_response["configuration"])
                    logger.success("Successfully parsed configuration data")
                except json.JSONDecodeError:
                    raise RuntimeError("Failed to parse configuration JSON data")
            else:
                raise RuntimeError("No configuration data found in response")

            # Process 'motor' section
            motor_data = config_data.get("motor", {}).get("Motors", [])
            self.parse_and_populate_motors(motor_data)

            # Process 'ai' section
            ai_data = config_data.get("ai", {}).get("AIs", [])
            logger.debug(f"Processing AI data: {len(ai_data)} items")
            self.parse_and_populate_ais(ai_data)

            return True

        except RuntimeError as e:
            # Catch RuntimeError and provide meaningful feedback
            logger.error(f"Runtime error occurred: {e}")
            logger.info("Possible solutions:")
            logger.info("1. Verify that the BCS ZeroMQ server is running and reachable.")
            logger.info(f"2. Check the connection to: {self.host}:{self.port}")

            raise

    # Synchronous version of populate_client_from_config for backward compatibility
    def populate_client_from_config(self):
        """Synchronous wrapper for populate_client_from_config_async"""
        try:
            # Create a new event loop for this function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the async population in the new event loop
            loop.run_until_complete(self.populate_client_from_config_async())

            # Clean up
            loop.close()
        except Exception as e:
            # Log error and exit
            logger.error(f"Error during client population: {e}")
            sys.exit(1)
        finally:
            # Restore the event loop
            asyncio.set_event_loop(None)

    # Parses and adds motors to the Happi client.
    def parse_and_populate_motors(self, motor_data):
        if not motor_data:
            logger.warning("No motor data found in the configuration.")
        else:
            ##################
            #     motors     #
            ##################
            logger.info(f"Processing {len(motor_data)} motors...")

            # iterates over each motor and adds to the DB
            for motor in motor_data:
                # Retrieves the name from the JSON
                name = motor.get("Name", "Unnamed Motor")

                # Copy of Original name, since we have to apply underscore
                # and lower case to create in happyDB
                originalName = name

                # sanitize name
                name = self._sanitize_name(name)

                general_params   = motor.get("General Parameters", {})
                itemType         = "motor"
                motor_params     = motor.get("Motor Parameters", {})
                prefix           = "MOTOR:FAKEPREFIX"

                ###############################
                # Args   - Position Arguments #
                ###############################
                
                args = ["no_args1", "no_args2", "no_args3"]

                ###############################
                # Kwargs - Keyword Arguments  #
                ###############################

                kwargs = {
                    "bridgeIP"          : self.host                        ,
                    "bridgePort"        : str(self.port)                   ,
                    "itemType"          : itemType                        ,
                    "name"              : name                            ,
                    "prefix"            : prefix                          ,
                    "originalName"      : originalName                    ,
                    "units"             : general_params.get("Units", "") ,
                }

                # Create and add motor item
                motor_item = self.client.create_item(
                    # Parameters for Args and Kwargs for BCSB Signal (ai) instantiation
                    args=args,
                    kwargs=kwargs,

                    # More Parameters
                    item_cls=OphydItem,
                    device_class="bcsophyd.zmq.bcs_motor.BCSMotor",
                    name=name.replace(" ", "_"),
                    prefix="MOTOR:FAKEPREFIX:",
                    bridgeIP=self.host,
                    itemType="motor",

                    #General Parameters
                    raw_offset=general_params.get("Raw Offset", 0),
                    invert=general_params.get("Invert?", False),
                    counts_per=general_params.get("Counts per", 1),
                    units=general_params.get("Units", ""),
                    convert_to=general_params.get("Convert to:", ""),
                    disable_when_not_moving=general_params.get("Disable When not Moving", False),
                    backlash_move_type=general_params.get("Backlash Move Type", ""),
                    backlash_move_size=general_params.get("Backlash Move Size (Units)", 0),
                    forward_sw_limit=general_params.get("Forward SW Limit (Units)", float("inf")),
                    reverse_sw_limit=general_params.get("Reverse SW Limit (Units)", float("-inf")),
                    motor_used=general_params.get("Motor Used?", False),
                    display_in_list=general_params.get("Display In List", False),
                    allow_set=general_params.get("Allow Set", False),
                    pull_in_moves=general_params.get("Pull In Moves", False),
                    number_of_retries=general_params.get("Number of Retries", 0),
                    deadband_units=general_params.get("Deadband (units)", 0),
                    motor_type=general_params.get("Type", "Controller"),
                    driver_name=general_params.get("Driver Name", ""),
                    groups=general_params.get("Groups", ""),
                    use_move_threshold=general_params.get("Use Move Threshold?", False),
                    threshold_units=general_params.get("Threshold (units)", 0),
                    display_precision_type=general_params.get("Display Precision Type", ""),
                    initial_goal=general_params.get("Initial Goal", False),
                    goal_units=general_params.get("Goal (Units)", 0),
                    precision=general_params.get("Precision", 4),
                    use_on_set_position=general_params.get("Use on Set Position", False),
                    complete_delay=general_params.get("Complete Delay", 0),
                    use_interlock=general_params.get("Use Interlock", False),
                    interlock_dio=general_params.get("Interlock DIO", ""),
                    use_move_test=general_params.get("Use Move Test", False),
                    move_test_dio=general_params.get("Move Test DIO", ""),
                    multiple_input=general_params.get("Multiple Input", False),
                    multiple_input_name=general_params.get("Multiple Input Name", ""),
                    can_do_flying_scan=general_params.get("Can Do Flying Scan", False),
                    user_level_visibility=general_params.get("User Level Visibility", 0),
                    min_ms=general_params.get("Min_ms", 0),

                    # Motor Parameters
                    velocity=motor_params.get("Velocity", 0),
                    accel=motor_params.get("Accel", 0),
                    decel=motor_params.get("Decel", 0),
                    fwd_limit=motor_params.get("Fwd Limit", ""),
                    rev_limit=motor_params.get("Rev Limit", ""),
                    max_velocity=motor_params.get("Max Velocity (c/s)", ""),
                    max_accel=motor_params.get("Max Accel (c/s^2)", ""),
                    max_decel=motor_params.get("Max Decel (c/s^2)", ""),
                    stop_decel=motor_params.get("Stop Decel (c/s^2)", ""),
                    encoder_resolution=motor_params.get("Encoder Resolution", 1),
                    percent=motor_params.get("Percent", 100),
                    delay=motor_params.get("Delay", 0),
                    flying_notifier=motor_params.get("Flying Pulses Notifier Name", ""),
                    fail_init=motor_params.get("Fail Init", 0),
                    fail_status=motor_params.get("Fail Status", 0),
                    fail_move=motor_params.get("Fail Move", 0)
                )

                self.client.add_item(motor_item)
                logger.debug(f"Added Motor: {name}")
            
            logger.success(f"Successfully processed {len(motor_data)} motors")

    # Parses and adds analog inputs (AIs) to the Happi client.
    def parse_and_populate_ais(self, ai_data):
        if not ai_data:
            logger.warning("No AI data found in the configuration.")
        else:
            ##############################
            #     analog inputs (ai)     #
            ##############################
            logger.info(f"Processing {len(ai_data)} analog inputs...")

            # iterates over each analog input (ai) and adds to the DB
            for ai in ai_data:
                # Retrieves the name from the JSON
                name = ai.get("Name", "Unnamed AI")

                # Copy of Original name, since we have to apply underscore
                # and lower case to create in happyDB
                originalName = name

                # sanitize name
                name = self._sanitize_name(name)

                general_settings = ai.get("General Settings", {})
                itemType         = "ai"
                parameters       = ai.get("Parameters", {})
                prefix           = "AI:FAKEPREFIX"
                units            = general_settings.get("Units", "Counts")
                
                ###############################
                # Args   - Position Arguments #
                ###############################

                args = ["no_args1", "no_args2", "no_args3"]

                ###############################
                # Kwargs - Keyword Arguments  #
                ###############################

                kwargs = {
                    "bridgeIP"     : self.host     ,
                    "bridgePort"   : str(self.port),
                    "itemType"     : itemType      ,
                    "name"         : name          ,
                    "prefix"       : prefix        ,
                    "originalName" : originalName  ,
                    "units"        : units         ,
                }

                # Create and add an analog (ai) item to the database
                ai_item = self.client.create_item(
                    # Parameters for Args and Kwargs for BCSB Signal (ai) instantiation
                    args=args,
                    kwargs=kwargs,

                    # More Parameters
                    bridgeIP=self.host,
                    bridgePort=str(self.port),
                    device_class="bcsophyd.zmq.bcs_signal.BCSSignal",
                    item_cls=OphydItem,
                    itemType=itemType,
                    name=name,
                    originalName=originalName,
                    prefix=prefix,

                    # Parameters
                    flying_notifier       = parameters.get("Flying Notifier", ""),
                    reset_notifier        = parameters.get("Reset Notifier" , ""),
                    
                    # General Settings
                    ai_type_name          = general_settings.get("AI Type Name", "Fake AI"),
                    amplifier_sensitivity = general_settings.get("Amplifier Sensitivity (A/V)", 1),
                    channel_used          = general_settings.get("Channel Used?", False),
                    groups                = general_settings.get("Groups", ""),
                    not_in_list           = general_settings.get("Not In List", False),
                    offset                = general_settings.get("Offset (V)", 0),
                    sensor_scale_factor   = general_settings.get("Sensor Scale Factor (Flux/Amps)", 1),
                    type                  = general_settings.get("Type", "Controller"),
                    units                 = general_settings.get("Units", "Counts"),
                )

                self.client.add_item(ai_item)
                logger.debug(f"Added AI: {name}")
            
            logger.success(f"Successfully processed {len(ai_data)} analog inputs")

    def _sanitize_name(self, name: str) -> str:
        # Sanitize name
        new_name = re.sub(r'\W|^(?=\d)', '_', name).lower()

        if new_name in self.seen_names:
            raise RuntimeError(
                f"A name collision occurred between new device '{name}' (-> '{new_name}') and a device named "
                f"'{self.seen_names[new_name]}' (-> '{new_name}'). This should be corrected in the LabVIEW device "
                f"setup. Keep in mind that names will be sanitized to be lowercase valid Python identifiers."
            )
        else:
            self.seen_names[new_name] = name
        return new_name