# i kinda wanted to make a video look like it was shot on 16mm
# so I made it a Python tool. Hours of work for something that takes 15 minutes! yay!

# steps:
# 1. split all frames
# 2. for every image:
#     2.1. apply signal processing to the images.
#         2.1.1. add red halation.
#         2.1.2. add it to the original via the 'lighten' blend mode
#     2.2. add a bit of noise
# 3. merge the output files again.

import os, argparse, numpy
from PIL import Image, ImageFilter
from tqdm import tqdm
from blend_modes import lighten_only

parser = argparse.ArgumentParser()
parser.add_argument("input", help="the video file to be processed")
parser.add_argument("-H", "--halation", type=int, help="the amount of halation. values between 6 and 20 tend to work well.", default=8)
parser.add_argument("-o", "--output", type=str, help="where to output the file to", default="out.mp4")
parser.add_argument("-n", "--noise", type=float, help="the intensity of the noise. must be between 0 and 1.", default=0.05)
args = parser.parse_args()

quiet = "> /dev/null 2>&1"

try:
    os.mkdir("temporary-frames")
    os.chdir("temporary-frames")
except FileExistsError:
    os.chdir("temporary-frames")
    os.system("rm *")

print("splitting frames...")

os.system(f"ffmpeg -i ../{args.input} frame-%6d.png" + quiet)

print("done splitting.")


for frame in tqdm(os.listdir(os.getcwd()), desc="converting frames"):
    im = Image.open(frame).convert("RGBA")
    
    empty_l = Image.new("L", im.size)
    white_l = Image.new("L", im.size, 255)
    
    red_halation = im.filter(ImageFilter.EDGE_ENHANCE).getchannel("R").filter(ImageFilter.GaussianBlur(args.halation))
    halation = Image.merge("RGBA", [red_halation, empty_l, empty_l, white_l])
    
    im_numpy = numpy.array(im).astype(float)
    ha_numpy = numpy.array(halation).astype(float)

    blended = numpy.uint8(lighten_only(im_numpy, ha_numpy, 1 - (1/args.halation)))

    composite = Image.fromarray(blended)

    noise = Image.effect_noise(im.size, 3).convert("RGBA")
    
    Image.blend(composite, noise, args.noise).filter(ImageFilter.GaussianBlur(0.8)).save("new-" + frame[6:])


print("stitching frames...")
os.system(f"ffmpeg -r 30 -i new-%6d.png -vcodec mpeg4 -y -vb 40M ../{args.output}.mp4" + quiet)
print("done.")
