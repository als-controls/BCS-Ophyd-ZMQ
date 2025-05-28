# Python Includes

# Module for writing asynchronous functions and managing event loops
import asyncio
# For interacting with the operating system
import os
# For generating random numbers
import random
# For interacting with the Python interpreter
import sys
# For working with time and delays
import time
# For handling multithreading
from   threading import Thread

# Bluesky Includes

# Core component for running data acquisition plans
from   bluesky           import RunEngine
# Provides useful default plots and summaries
from   bluesky.callbacks.best_effort import BestEffortCallback
# Enables real-time plotting of data
from   bluesky.callbacks import LivePlot
# Displays tabular data in real-time
from   bluesky.callbacks import LiveTable

# standard scan plans for experiments
from   bluesky.plans     import grid_scan, scan
from   bluesky.plans     import count, fly
# Alias for importing all plans provided by Bluesky
import bluesky.plans     as bp
from bluesky.preprocessors import fly_during_wrapper
from bluesky.preprocessors import monitor_during_wrapper

# Ophyd Includes

# Base classes for creating and managing hardware devices
from ophyd import Component, Device, Signal
# Interface for controlling physical motors
from ophyd import EpicsMotor
# Simulated devices for testing and development
from ophyd.sim import det, motor
# Tools for creating fake EPICS motors
#from ophyd.sim import FakeEpicsMotor
from ophyd.sim import make_fake_device
# Simulated Gaussian signal device
from ophyd.sim import SynGauss

# Client for managing device configuration in Happi

from happi import Client, OphydItem, from_container

# BCS Includes

# BCS Includes
from src.bcsophyd.zmq.bcs_server import BCSServer

# BCS 2D Detector uses FastaAPI
from src.bcsophyd.zmq.bcs_area_detector import BCSAreaDetector
# Device manager for Happi database integration
from src.bcsophyd.zmq.bcs_device_manager import BCSDeviceManager

# BCS-specific motor implementation
from src.bcsophyd.zmq.bcs_motor import BCSMotor
# BCS-specific signal implementation
from src.bcsophyd.zmq.bcs_signal import BCSSignal

async def classTest_BCSDeviceManager(host, port):

    """
    Test the BCSDeviceManager class with proper async handling
    """
    print(f"Testing BCSDeviceManager with host={host}, port={port}")
    
    # Create the BCSDeviceManager instance - this just initializes it
    print("Creating BCSDeviceManager instance...")
    bcsDeviceManager = BCSDeviceManager(host=host, port=port)
    
    # Connect to server and populate database - this is the async part
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False
    
    print("AIs and Motors added to the Happi DB!")
    
    # Iterate over all devices
    print("Printing all devices (AIs and Motors)...")
    for device in bcsDeviceManager.client.items():
        print(device)

    print("\n\n\n")

    # Search for AIs by name and instantiating them
    print("Searching for devices (AIs) by name:")
    results = bcsDeviceManager.client.search_regex(name="new_ai_2")

    # Looping Over Results
    for device in results:
        print(device)
        tempAI = device.get()
        print("AI instantiated...")
        print("Printing AI device...")
        print(tempAI)

    # Search for Motors by name and instantiating them
    print("Searching for devices (Motors) by name:")
    results = bcsDeviceManager.client.search_regex(name="Motor2")
    print("End of Search")

    for device in results:
        print(device)
        tempMotor = device.get()
        print(tempMotor)
        
    return True


async def classTest_BCSServer(host, port):

    """Test connection to a BCS ZeroMQ server"""
    print(f"Testing connection to BCS ZeroMQ server at {host}:{port}...")
    
    bcs_server = BCSServer()
    connected = False

    try:
        # Note: The original code was using self.bcs_server and self.host/self.port
        # which doesn't make sense in a standalone function - fixing that
        await bcs_server.connect(host, port)
        connected = True
        print(f"✓ Successfully connected to BCS ZeroMQ server at {host}:{port}")
        
        # Optional: Test a simple command
        response = await bcs_server.test_connection()
        print(f"Test connection response: {response}")
        
        return True
    except Exception as e:
        print(f"✗ Error connecting to BCS ZeroMQ server: {e}")
        raise

# Tests BCSSignal, analogous to EpicsSignal 
async def classTest_BCSSignal(host, port):
    """
    Test the BCSSignal class with async handling.
    
    This function demonstrates how to properly use async/await patterns
    when working with both synchronous and asynchronous operations.
    
    Args:
        host (str): The BCS server host address
        port (int): The BCS server port
        
    Returns:
        bool: Success status of the test
    """
    # Create a BCSDeviceManager instance
    # This is a synchronous operation (regular function call)
    # No need for await here since the constructor is not async
    bcsDeviceManager = BCSDeviceManager(host, port)

    # Connect to server and populate database
    # This IS an async operation, so we need to await it
    # The connect() method is defined with `async def`, which means
    # it returns a coroutine that must be awaited to get the result
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False

    print("AIs and Motors added to the Happi DB!")
    
    # Searching the Happi database
    # This is a synchronous operation (regular method call)
    # search_regex is a regular method, not async, so no await needed
    print("Searching for devices (AIs) by name:")
    results = bcsDeviceManager.client.search_regex(name="new_ai_2")

    if not results:
        print("No devices found matching 'new_ai_2'")
        print("Available devices:")
        for device in bcsDeviceManager.client.items():
            print(f"  - {device}")
        return False

    # Looping Over Results
    for ai in results:
        print(ai)
        
        # Get the device (instantiate it)
        # This is a synchronous operation from the Happi library
        # ai.get() returns an actual object, not a coroutine, so no await
        tempAI = ai.get()
        
        print("AI instantiated...")
        print("Printing AI device...")
        print(tempAI)
        
        try:
            print("Retrieving value with get():")
            
            # Call the get() method of the BCSSignal object
            # This IS an async operation, so we need to await it
            # tempAI.get() is defined as `async def get(self)`, which means 
            # it returns a coroutine that must be awaited to get the actual value
            #
            # WRONG WAY: value = asyncio.run(tempAI.get())
            # - asyncio.run creates a new event loop, which is not allowed inside an async function
            # - It would try to create a nested event loop, causing errors
            #
            # RIGHT WAY: use await directly
            value = await tempAI.get()
            
            print(f"Value = {value}")
            
            # Let's also test the read() method (which Bluesky uses)
            # This is also async, so we need to await it
            print("Testing read() method...")
            read_result = await tempAI.read()
            print(f"Read result: {read_result}")
            
        except Exception as e:
            print(f"Error accessing signal: {e}")
            import traceback
            traceback.print_exc()
            
        print("======")
    
    return True

# Tests BCSMotor, analogous to EpicsMotor
async def classTest_BCSMotor(host, port):
    """
    Test the BCSMotor class with async handling.
    
    This function demonstrates proper use of async/await patterns
    when working with BCSMotors in a Bluesky environment.
    
    Args:
        host (str): The BCS server host address
        port (int): The BCS server port
        
    Returns:
        bool: Success status of the test
    """
    # Create a BCSDeviceManager instance (synchronous operation)
    bcsDeviceManager = BCSDeviceManager(host, port)

    # Connect to server and populate database (async operation)
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False

    print("AIs and Motors added to the Happi DB!")
    
    # Search for motors by name (synchronous operation)
    print("Searching for devices (Motors) by name:")
    results = bcsDeviceManager.client.search_regex(name="Motor2")

    if not results:
        print("No motors found matching 'Motor2'")
        print("Available devices:")
        for device in bcsDeviceManager.client.items():
            print(f"  - {device}")
        return False

    # Looping over results
    for motor_item in results:
        print(motor_item)
        
        # Get the motor instance (synchronous operation)
        tempMotor = motor_item.get()
        
        print("Motor instantiated...")
        print("Printing Motor device...")
        print(tempMotor)
        
        try:
            print("Retrieving position value:")
            
            # If the motor's get() method is async (which it should be), use await
            # If it's synchronous, remove the await keyword
            position = tempMotor.get()
            print(f"Position = {position}")
            
            # Test other motor methods
            print("\nTesting read() method:")
            read_result = await tempMotor.read()
            print(f"Read result: {read_result}")
            
            # Uncomment to test motor movement
            # print("\nTesting move to a new position:")
            # await tempMotor.set(position + 1.0)  # Move 1 unit forward
            # print("Move command sent")
            
        except Exception as e:
            print(f"Error accessing motor: {e}")
            import traceback
            traceback.print_exc()
            
        print("======")
    
    return True

# Pure Bluesky Ophyd Scan
# Uses a simulated det and motor
# from ophyd.sim import det, motor
def scan_SimMotor_SimDet():

    # Initialize the RunEngine
    RE = RunEngine({})

    # Set up a simple LiveTable to display scan results
    live_table = LiveTable(['motor', 'det'])

    # Add the callback to the RunEngine
    RE.subscribe(live_table)

    # Perform a simple scan
    # Scan 'motor' from 0 to 10 in 11 steps and read 'det'
    RE(scan([det], motor, 0, 10, 11))

# A BlueSky-based scan function simulating data acquisition using a fake motor
# and a fake EPICS device detector that generates random integer signals.
def scan_FakeMotor_FakeDetWithFakeEpicsSignal():

    # This simulates a hardware signal that a detector might produce in real experiments.
    # Custom Signal that generates random integers between 0 and 99
    class RandomSignal(Signal):
        def get(self):
            return random.randint(0, 99)

    # Wrapper Device for the random signal
    # Simulates an EPICS device that has a single random integer signal.
    class FakeEpicsDevice(Device):
        random_int = Component(RandomSignal, kind="hinted")

    # Initialize the BlueSky RunEngine
    # This is the central control system for orchestrating data acquisition.
    RE = RunEngine()

    # Attach a BestEffortCallback
    # This callback provides live feedback during scans, such as plotting and tabular data.
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Uses a simulated motor see import below
    # from ophyd.sim import det, motor
    myMotor = motor

    # Create an instance of the fake EPICS device
    # The `fake_device` serves as the simulated detector producing random data.
    fake_device = FakeEpicsDevice(name="fake_device_detector")

    # Perform a scan including the fake device
    # This scan runs over the motor positions from 1 to 5, taking 20 steps.
    # At each position, it collects data from the fake EPICS device.
    print("Running a scan with a fake EPICS device...")
    RE(scan([fake_device], myMotor, 1, 5, 20))

# A BlueSky-based scan function simulating data acquisition using a fake motor
# however using an analog input (ai) coming from labview
async def scan_SimMotor_AiDevice(host, port):

    # Initialize a BCSDeviceManager
    # This connects to a Happi database to manage and retrieve EPICS devices.
    bcsDeviceManager = BCSDeviceManager(host, port) #HappiDB

    # Connect to server and populate database (async operation)
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False

    print("AIs and Motors added to the Happi DB!")

    # Search for the desired EPICS device in the Happi database using a regex match
    # The search is looking for a device with the name "new_ai_2".
    results = bcsDeviceManager.client.search_regex(name="new_ai_2")

    print("Result ", results)

    # Get the first matching device object from the search results
    # `myAI2` represents an existing EPICS signal tied to a real device.
    myAI2 = results[0].get()

    # Dynamically create a Device and attach the existing signal object
    # This creates a virtual detector by wrapping the signal in a device structure.
    fake_device = Device(name="fake_device")
    # Attach the signal to the device dynamically
    fake_device.ai2 = myAI2  

    # Mark the signal as hinted so it appears in the primary data stream
    # BlueSky uses this property to decide which data to highlight during scans.
    fake_device.ai2.kind = "hinted"

    # Initialize the BlueSky RunEngine
    # The RunEngine orchestrates the execution of the scan plan.
    RE = RunEngine()

    # Attach a BestEffortCallback
    # This callback provides live feedback, including plots and tabular data.
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Uses a simulated motor
    # from ophyd.sim import det, motor
    myMotor = motor

    # Perform a scan including the fake device
    # The scan moves the motor from position 0 to 1 in 10 steps and collects
    # data from the `ai2` signal of the fake device at each position.
    print("Running a scan with a fake EPICS device...")
    RE(scan([fake_device.ai2], myMotor, 0, 1, 11))
    

# Pure Bluesky Code
# A BlueSky-based scan function that uses a real Epics Motor
# This Epics Motor comes from LabView
# and a simulated detector from Ophyd
def scan_RealEpicsMotor_SimDet():

    # Define the EPICS motor
    motor = EpicsMotor("de:Motor1", name="motor")

    # Check connection
    # The `.connected` attribute confirms if the motor is connected to EPICS.
    print(f"Motor connected: {motor.connected}")
    # Wait for up to 5 seconds to establish a connection
    motor.wait_for_connection(timeout=5)
    print(f"Motor connected after wait: {motor.connected}")

    # Check and display the current position of the motor
    # This ensures the motor's position can be read before starting the scan.
    print(f"Motor position: {motor.position}")

    # Initialize the BlueSky Run Engine
    # The RunEngine coordinates scan execution and manages data acquisition.c
    RE = RunEngine()

    # Attach a LiveTable to the RunEngine
    # The `LiveTable` provides real-time tabular feedback on scan data,
    # displaying values for the motor and detector.
    live_table = LiveTable([det,motor])
    RE.subscribe(live_table)

    # Define parameters for a linear scan
    # `start` and `stop` specify the range of motor positions, and `num_steps`
    # determines the number of positions sampled during the scan.
    start = 0      # Starting position
    stop  = 300    # Stopping position
    num_steps = 4  # Number of steps in the scan

    # Execute the scan
    # The `scan` plan moves the motor from `start` to `stop` in `num_steps` and
    # collects data from the detector at each step.
    RE(scan([det], motor, start, stop, num_steps))

# A BlueSky-based scan function that uses a real motor 
# fetched from BCSDeviceManager (uses Happi)
async def scan_BCSMotor_SimDet(host, port):

    # When testing locally development
    #ip = "127.0.0.1"

    # Initialize the BCSDeviceManager
    # The BCSDeviceManager interfaces with the Happi database to retrieve device configurations.
    bcsDeviceManager = BCSDeviceManager(host, port) #HappiDB

    # Connect to server and populate database (async operation)
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False

    print("AIs and Motors added to the Happi DB!")

    # Retrieve the first matching device object from the search results

    # Local Test Motor
    results = bcsDeviceManager.client.search_regex(name="Motor3")

    # Retrieve the first matching device object from the search results
    myBCSMotor = results[0].get()

    # Print details of the motor for verificationc
    print(myBCSMotor)

    # Initialize the BlueSky Run Engine
    # The RunEngine orchestrates the execution of the scan plan.c
    RE = RunEngine()

    # Attach a LiveTable to the RunEngine
    # The `LiveTable` provides real-time tabular feedback on scan data,
    # displaying values for the motor and detector during the scan.c
    live_table = LiveTable([det,myBCSMotor])
    RE.subscribe(live_table)

    # Define parameters for a linear scan
    # The motor will move from `start` to `stop` over `num_steps` positions.
    start     = 40   # Starting position
    stop      = 50   # Stopping position
    num_steps = 11   # Number of steps in the scan

    # Execute the scan
    # The `scan` plan moves the motor over the specified range and collects
    # data from the detector at each position.
    RE(scan([det], myBCSMotor, start, stop, num_steps))

async def scan_BCSMotor_SimDet_WithInterruption(host, port):
    """
    BlueSky-based scan function with a real motor fetched from BCSDeviceManager (uses Happi).
    Includes functionality to interrupt the scan after a delay.
    """

    # Initialize the BCSDeviceManager
    bcsDeviceManager = BCSDeviceManager(host, port)

    # Connect to server and populate database (async operation)
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False

    print("AIs and Motors added to the Happi DB!")

    # Retrieve the first matching device object from the search results
    results = bcsDeviceManager.client.search_regex(name="Motor3")
    myBCSMotor = results[0].get()  # Get the motor object

    # Print details of the motor for verification
    print("Using motor:", myBCSMotor)

    # Initialize the BlueSky Run Engine
    RE = RunEngine()

    # Attach a LiveTable to the RunEngine
    live_table = LiveTable([det, myBCSMotor])
    RE.subscribe(live_table)

    # Define parameters for a linear scan
    start = 40  # Starting position
    stop = 1000   # Stopping position
    num_steps = 11  # Number of steps in the scan

    # Function to interrupt the scan after a delay
    def interrupt_run():
        time.sleep(3)  # Wait 2 seconds before stopping
        print("Interrupting the scan...")
        #myBCSMotor.stop()
        RE.stop()  # Issue the stop command , wait safe state
        #RE.halt()  # Issue IMMEDIATELY stop command, does not wait for point in the scan

    # Launch the interrupt in a separate thread
    interrupt_thread = Thread(target=interrupt_run)
    interrupt_thread.start()

    # Execute the scan
    try:
        print("Starting scan...")
        RE(scan([det], myBCSMotor, start, stop, num_steps))
    except Exception as e:
        print(f"Scan interrupted with exception: {e}")

    # Ensure the interrupt thread completes
    interrupt_thread.join()
    print("Scan complete.")

# A BlueSky-based dual scan function that uses a real motor coming from Labview
# fetched from BCSDeviceManager (uses Happi)
async def scan_gridScan_TwoBCSMotors_SimDet(host, port):

    # Initialize the BCSDeviceManager
    # The BCSDeviceManager interfaces with the Happi database to retrieve device configurations.
    bcsDeviceManager = BCSDeviceManager(host, port) #HappiDB

    # Connect to server and populate database (async operation)
    print("Connecting to BCS server and populating device database...")
    success = await bcsDeviceManager.connect()
    
    if not success:
        print("Failed to connect to BCS server or populate device database")
        return False

    print("AIs and Motors added to the Happi DB!")

    # Retrieve the first matching device object from the search results

    # Local Test Motor
    results = bcsDeviceManager.client.search_regex(name="Motor3")

    # Retrieve the first matching device object from the search results
    motor3 = results[0].get()

    # Local Test Motor
    results = bcsDeviceManager.client.search_regex(name="Motor4")

    # Retrieve the first matching device object from the search results
    motor4 = results[0].get()

    # Initialize the BlueSky Run Engine
    # The RunEngine orchestrates the execution of the scan plan.c
    RE = RunEngine()

    # Attach a LiveTable to the RunEngine
    # The `LiveTable` provides real-time tabular feedback on scan data,
    # displaying values for the motor and detector during the scan.c
    live_table = LiveTable([det,motor3, motor4])
    RE.subscribe(live_table)

    # Define grid scan parameters
    motor3_start = 0  # Starting position for motor1 (X-axis)
    motor3_stop  = 5  # Stopping position for motor1
    motor3_steps = 6  # Number of steps for motor1

    motor4_start = 0  # Starting position for motor2 (Y-axis)
    motor4_stop  = 2  # Stopping position for motor2
    motor4_steps = 3  # Number of steps for motor2

    snake = True      # Set to True for a "snaking" pattern, False for raster

    # Execute the grid scan
    # `grid_scan` moves motor1 in steps for each step of motor2 and collects data at each position
    RE(grid_scan([det], motor3, motor3_start, motor3_stop, motor3_steps,
                         motor4, motor4_start, motor4_stop, motor4_steps, snake))

def scan_SimMotor_BCSAreaDetector():

    """
    Test function to check if we can perform a basic scan
    with the BCS2DDetector class and print results in a table.
    """

    # Instantiate the detector
    bcsDetector = BCSAreaDetector(name="myBCSAreaDetector")

    # Create a RunEngine instance
    RE = RunEngine({})

    # Attach a LiveTable callback to the RunEngine
    # It will display the motor position and the detector's pixel sum
    live_table = LiveTable([motor,bcsDetector])
    RE.subscribe(live_table)

    # Perform a simple scan: move a motor while acquiring images
    print("Starting scan...")
    RE(scan([bcsDetector], motor, -1, 1, 11))


def fly_scan_SimMotor_BCSAreaDetector():

    # Instantiate the detector
    bcsDetector = BCSAreaDetector(name="myBCSAreaDetector")

    # Create a RunEngine instance
    RE = RunEngine({})

    # Add BestEffortCallback
    #bec = BestEffortCallback()
    #RE.subscribe(bec)

    # Create LiveTable showing motor position and total_intensity
    live_table = LiveTable([motor, f'{bcsDetector.name}_total_intensity'])  # Use full signal name
    RE.subscribe(live_table)

    print("Starting fly scan...")
    RE(monitor_during_wrapper(
        scan([bcsDetector], motor, -1, 1, 11),
        [bcsDetector.total_intensity]
    ))

def fly_scan_RealEpicsMotor_BCSAreaDetector():

    # Define the EPICS motor
    flying_motor = EpicsMotor("de:Motor1", name="motor")

    # Check connection
    # The `.connected` attribute confirms if the motor is connected to EPICS.
    print(f"Motor connected: {flying_motor.connected}")
    # Wait for up to 5 seconds to establish a connection
    flying_motor.wait_for_connection(timeout=5)
    print(f"Motor connected after wait: {motor.connected}")

    # Check and display the current position of the motor
    # This ensures the motor's position can be read before starting the scan.
    print(f"Motor position: {flying_motor.position}")

    # Instantiate the detector
    bcsDetector = BCSAreaDetector(name="myBCSAreaDetector")

    # Create a RunEngine instance
    RE = RunEngine({})
    
    # Create LiveTable showing motor position and total_intensity
    live_table = LiveTable([flying_motor, f'{bcsDetector.name}_total_intensity'])  # Use full signal name

    RE.subscribe(live_table)

    print("Starting fly scan...")

    RE(fly([bcsDetector]))
    
async def run_all_tests(host, port):

    # Testing BCS Server
    #await classTest_BCSServer(host, port)

    # Tests - BCS Standalone Classes 
    #await classTest_BCSDeviceManager(host, port)
    #await classTest_BCSSignal(host, port)
    #await classTest_BCSMotor(host, port)
    
    # Scan Tests
    #scan_SimMotor_SimDet()                                 # Bluesky Only
    #scan_FakeMotor_FakeDetWithFakeEpicsSignal()            # Bluesky Only
    #scan_RealEpicsMotor_SimDet()                           # Hybrid
    
    # Tests - BCS Scans
    #await scan_SimMotor_AiDevice(host, port)               # Hybrid
    #await scan_BCSMotor_SimDet(host,port)                  # Hybrid
    #await scan_BCSMotor_SimDet_WithInterruption(host,port) # Hybrid
    await scan_gridScan_TwoBCSMotors_SimDet(host,port)     # Hybrid

    # Tests - Currently does not use BCS
    #scan_SimMotor_BCSAreaDetector()             # Under Development
    #fly_scan_SimMotor_BCSAreaDetector()         # Under Development
    #fly_scan_RealEpicsMotor_BCSAreaDetector()   # Under Development


def main():

    host = "192.168.195.129"
    port = 5577
    
    print(f"Starting tests with host={host}, port={port}")
    
    # Run all tests in a single asyncio.run call
    try:
        asyncio.run(run_all_tests(host, port))
        print("All tests completed successfully")
    except Exception as e:
        print(f"Tests failed with error: {e}")

if __name__ == "__main__":

    main()