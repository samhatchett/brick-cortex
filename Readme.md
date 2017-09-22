# Brick Cortex

This is an experiment. Can you train an AI on 3d-rendered images, and then sucessfully classify LEGO pieces in real-life? I have no idea.

## training-set-generator
This is a docker container that generates lots of 3-d rendered LEGO pieces, viewed from various angles. It uses ReBrickable's inventory of sets to establish a list of valid part-color combinations, then passes ldraw parts through l3p and then pov-ray.
The `pov` files are generated for several viewing angles, but should probably also be differently lit, with different backgrounds as well.

## brick-train
(work in progress) - Uses Keras to train a CNN using the rendered images. Should use tagging or multi-class classification.

