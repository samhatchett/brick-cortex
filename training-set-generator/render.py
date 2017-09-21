import os
import sys
import re
import subprocess
import numpy
import sqlite3
from pathlib import Path
import shutil

most_common_first = True

conn = sqlite3.connect('/app/inventory.db')
c = conn.cursor()

background_opt = "-b.9,.9,.9" # gray background
lights_include_opt = "-il/app/lights.pov"
height_opt = '+H480'
width_opt = '+W640'


povfile_re = re.compile('\.pov', re.IGNORECASE)



radius = -50
lats = [-70,-50,-30,30,50,70]
#lats = numpy.arange(-70, 70, 20)
lons = numpy.arange(-180, 170, 45)

# debug stuff
#lats = [45]
#lons = [90]


# get color lookups - we will use the hex values allowed by l3p
color_lookup = {} # key: integer, value: hex color
for row in c.execute("select id, name, rgb, is_trans from colors"):
    prefix = "0x02"
    is_trans = False
    if row[3] == 't':
        # transparent
        prefix = "0x03"
        is_trans = True
    hex_color = row[2]
    color_id = row[0]
    color_lookup[color_id] = {'hex': "{}{}".format(prefix, hex_color), 'name': row[1], 'transparent': is_trans}


os.chdir('/data')
if Path('img').exists():
    #shutil.rmtree('/data/img')
    print("dir exists")
else:
    os.mkdir('img')

os.chdir('/data/img')

# go through inventory and only generate images that are valid part/color combinations
#c.execute("select part_num, name from parts where part_cat_id not in (13,17,27,57)")
#part_rows = c.fetchall()

q = "select p.name, i.part_num, i.color_id, sum(i.quantity) as count from inventory_parts i join parts p USING(part_num) where p.part_cat_id not in (13,17,27,57) group by part_num, color_id order by count desc"
# name, part color, count

c.execute(q)
part_rows = c.fetchall()

# track how far we've gone
part_num = 0
part_count = len(part_rows)

for p_row in part_rows:
    part_name = p_row[0].encode('utf-8','ignore')
    part = p_row[1]
    color = p_row[2]

    part_num += 1
    pctDone = part_num / part_count
    print("### PART {} OF {} ( {:.3f}% complete )".format(part_num, part_count, pctDone))
    sys.stdout.flush()

    os.chdir('/data/img')
    # check if the part is in the ldraw library
    part_name_path = "{}-[{}]".format(part, part_name)
    part_name_path = part_name_path.replace("/","-")
    part_name_path = part_name_path.replace(" ","_")
    part_file = Path("/opt/ldraw/parts", part).with_suffix('.dat')
    if not part_file.is_file():
        #something is wrong. resolve re-named parts somehow?
        print("OOPS - part {} could not be found!".format(part))
        continue

    if not Path(part).exists():
        os.mkdir(part)

    # get hex value of color:
    color_hex = color_lookup[color]['hex']
    color_name = color_lookup[color]['name']
    trans = color_lookup[color]['transparent']
    color_name.replace(" ", "_")
    os.chdir("/data/img/{}".format(part))
    if not Path(color_name).exists():
        os.mkdir(color_name)
    os.chdir("/data/img/{}/{}".format(part, color_name))
    print("rendering -- part: {} -> color: {} ({})".format(part_name_path, color_name, "Transparent" if trans else "Opaque"))
    sys.stdout.flush()
    fname = "{}.dat".format(part)
    for lat in lats:
        for lon in lons:
            if lon == -180:
                lon = -179  # silly bug? sometimes camera is not pointed at part
            pov_fname = "{}_{}_{}.pov".format(part, lat, lon)
            out_fname = "{}_{}_{}.png".format(part, lat, lon)
            out_fname_opt = "+O{}".format(out_fname)
            color_opt = "-c{}".format(color_hex)
            cg_opt = "-cg{},{},{}".format(lat, lon, radius)
            # does the output file already exist?
            if Path(out_fname).exists():
                print("{} exists. skipping.".format(out_fname))
                continue
            l3p_cmd = ['l3p', background_opt, '-q4', color_opt, lights_include_opt, cg_opt, '-bu', '-o', fname, pov_fname]
            pov_cmd = ['povray', height_opt, width_opt, '+A', '+Q9', '-GA', pov_fname, out_fname_opt]
            subprocess.call(l3p_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            #subprocess.call(pov_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            #try:
            #    os.remove(pov_fname)
            #except:
            #    print("couldn't remove {}".format(pov_fname))





# all done with the l3p generation.
# now start on processing bathces of POV-ray files
import threading
import time

max_cpu = 4
processing = 0

def call_batch(command):
    global processing
    print("running POV-ray:")
    print(command)
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.wait()
    processing -= 1


os.chdir('/data')
if Path('ren').exists():
    print("dir ren exists")
else:
    os.mkdir('ren')

os.chdir('/data/ren')
for root, dirs, files in os.walk('/data/img'):
    for f in files:
        file = os.path.join(root, f)
        filename, file_extension = os.path.splitext(f)
        ext = file_extension[1:]
        if ext == 'pov':
            while processing > max_cpu:
                time.sleep(1)
            print("looking at file: {}".format(file))
            pov_fname = file
            rendered_root = root.replace("/img/", "/ren/")
            out_fname = str(Path(rendered_root, filename).with_suffix('.png'))
            out_fname_opt = "+O{}".format(out_fname)
            os.makedirs(rendered_root,exist_ok=True)
            pov_cmd = ['povray', height_opt, width_opt, '+A', '+Q9', '-GA', pov_fname, out_fname_opt]
            if Path(out_fname).exists():
                print("{} exists. skipping.".format(out_fname))
            else:
                t = threading.Thread(target=call_batch, args=(pov_cmd,))
                t.daemon = True
                t.start()
                processing += 1




# l3p -bWhite -q4 -c4 -cg10,45,-50 -o 27c.dat pov/ && cd pov && povray +H480 +W640 +A +Q9 *.pov

        # l3p -bWhite -q4 -c4 -cg50,45,-50 -o 11598.dat && povray +H480 +W640 +A +Q9 -GA 11598.pov