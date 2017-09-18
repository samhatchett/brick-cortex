# BrickSmarts training set generator

This tool generates Lego part images - multiple viewing angles of every Lego piece in the LDRAW database, in every color.

# Why?

You know. I'm training my AI.

# How?

Download it. Build and run the Docker container. It will take a long time to generate all the images.

```
docker build -t lego-training-set .
docker run -d -v /path/to/images:/data -lego-training-set
```

