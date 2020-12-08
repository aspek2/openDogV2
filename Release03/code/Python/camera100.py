import RPi.GPIO as GPIO
import jetson.inference
import jetson.utils

import time

import argparse
import sys

def get_arguments():
	# parse the command line
	parser = argparse.ArgumentParser(description="Locate objects in a live camera stream using an object detection DNN.", 
					 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.detectNet.Usage() +
					 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())

	parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
	parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
	parser.add_argument("--network", type=str, default="ssd-mobilenet-v2", help="pre-trained model to load (see below for options)")
	parser.add_argument("--overlay", type=str, default="box,labels,conf", help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'")
	parser.add_argument("--threshold", type=float, default=0.5, help="minimum detection threshold to use") 

	is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

	try:
		opt = parser.parse_known_args()[0]
	except:
		print("")
		parser.print_help()
		sys.exit(0)
	return opt

def load_model(opt):

	# load the object detection network
	net = jetson.inference.detectNet(opt.network, sys.argv, opt.threshold)

def create_video_sources(opt):
	# create video sources & outputs
	input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
	output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv+is_headless)
	return input, output

# ------------------------------------------------ #
# GPIO Pin functions
# ------------------------------------------------ #

def init_output_pins(pin_nums):
	for pin_num in pin_nums:
		GPIO.setup(pin_num, GPIO.OUT, initial=GPIO.HIGH)
		GPIO.output(pin_num, GPIO.HIGH)

def initialise_GPIO():
	#setup GPIO pins
	input_pins = []
	output_pins = [18,17,16,20,21]
	
	GPIO.setmode(GPIO.BCM) #RaspPi pin numbering
	
	init_output_pin(output_pins)
	
def reset_pins(pin_nums):
	for pin_num in pin_nums:
		GPIO.output(pin_num, GPIO.HIGH)
	print("reset_pins")

def back():
	nothing()
	GPIO.output(18, GPIO.LOW)
	print("back")

def forward():
	reset_pins()
	GPIO.output(17, GPIO.LOW)
	print("forward")

def left():
	reset_pins()
	GPIO.output(16, GPIO.LOW)
	print("left")

def right():
	reset_pins()
	GPIO.output(20, GPIO.LOW)
	print("right")

def up():
	reset_pins()
	GPIO.output(21, GPIO.LOW)
	print("up")
	
# ------------------------------------------------ #
def main():
	opt = get_arguments()
	
	# NN model
	load_model(opt)
	# video
	input, output = create_video_sources(opt)
	# GPIO
	initialise_GPIO()
	
	# declare variables as global and that
	global index
	global width
	global location
	global confidence
	index = 0
	width = 0
	location = 0
	condifence = 0;

	# process frames until the user exits
	while True:

		# capture the next image
		img = input.Capture()

		# detect objects in the image (with overlay)
		detections = net.Detect(img, overlay=opt.overlay)

		# print the detections
		#print("detected {:d} objects in image".format(len(detections)))

		# check for detections, otherwise nothing	

		if(len(detections) > 0):
			print("object detected")
			for detection in detections:
				index = detections[0].ClassID
				confidence = (detections[0].Confidence)
				width = (detections[0].Width)
				location = (detections[0].Center[0])

				# print index of item, width and horizonal location

				print(index)
				print(width)
				print(location)
				print(confidence)

				# look for detections

				if (index == 1 and confidence > 0.9):
					back()

				elif (index == 2 and confidence > 0.7):
					forward()

				elif (index == 3 and confidence > 0.7):
					left()

				elif (index == 4 and confidence > 0.7):
					right()

				elif (index == 5 and confidence > 0.7):
					up()

		else:
			nothing()	# nothing is detected


		# render the image
		output.Render(img)

		# update the title bar
		output.SetStatus("{:s} | Network {:.0f} FPS".format(opt.network, net.GetNetworkFPS()))

		# print out performance info
		#net.PrintProfilerTimes()

		# exit on input/output EOS
		if not input.IsStreaming() or not output.IsStreaming():
			break

if __name__ == "__main__":
	main()
